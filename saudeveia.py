import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import io

# --- 1. CONFIGURAÇÕES ---
URL_BASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
HEADERS = {
    "apikey": API_KEY, 
    "Authorization": f"Bearer {API_KEY}", 
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def enviar_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM/sendMessage", 
                      json={"chat_id": "5256921022", "text": msg}, timeout=5)
    except: pass

@st.cache_data(ttl=1)
def buscar_dados(tabela):
    try:
        res = requests.get(f"{URL_BASE}{tabela}?select=*", headers=HEADERS, timeout=10)
        return pd.DataFrame(res.json()) if res.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

# --- 2. INTERFACE E CSS SEGURO ---
st.set_page_config(page_title="Saúde Rock - Gestão Real", layout="centered")

# CSS focado apenas em aproveitar melhor o espaço, sem quebrar o layout nativo
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; padding-left: 1rem; padding-right: 1rem; }
    .stButton button { width: 100%; }
    .stAlert { padding: 0.5rem !important; margin-bottom: 0.5rem !important; }
    </style>
""", unsafe_allow_html=True)

if "autenticado" not in st.session_state: st.session_state.autenticado = False

with st.sidebar:
    st.title("🛡️ Sistema")
    if not st.session_state.autenticado:
        senha = st.text_input("Senha ADM", type="password")
        if st.button("Acessar") or senha == "1234":
            if senha == "1234": st.session_state.autenticado = True; st.rerun()
    else:
        if st.button("Sair do Modo ADM", use_container_width=True):
            st.session_state.autenticado = False; st.rerun()
    
    st.divider()
    aba = st.radio("Navegação", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"])

# --- 3. TELAS ---

if aba == "Estoque":
    st.subheader("📋 Status do Estoque")
    df = buscar_dados("remedios")
    if not df.empty:
        hoje = datetime.now()
        for _, r in df.iterrows():
            ini = pd.to_datetime(r['data_inicio'])
            passados = (hoje - ini).days
            dose = float(r['dose_diaria'])
            atual = max(0.0, float(r['qtd_total']) - (passados * dose))
            resta_dias = float(atual / dose) if dose > 0 else 0
            data_fim = hoje + timedelta(days=resta_dias)
            
            with st.container(border=True):
                st.markdown(f"**💊 {r['nome'].upper()}**")
                
                # Painel de métricas usando HTML Flexível (Perfeito para celular e PC)
                html_metricas = f"""
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-top: 1px solid rgba(128,128,128,0.2); border-bottom: 1px solid rgba(128,128,128,0.2); margin-bottom: 10px;">
                    <div style="text-align: center; width: 33%;">
                        <div style="font-size: 0.8rem; opacity: 0.8;">Estoque</div>
                        <div style="font-size: 1.2rem; font-weight: bold;">{atual:g}</div>
                    </div>
                    <div style="text-align: center; width: 33%; border-left: 1px solid rgba(128,128,128,0.2); border-right: 1px solid rgba(128,128,128,0.2);">
                        <div style="font-size: 0.8rem; opacity: 0.8;">Dose/Dia</div>
                        <div style="font-size: 1.2rem; font-weight: bold;">{dose:g}</div>
                    </div>
                    <div style="text-align: center; width: 33%;">
                        <div style="font-size: 0.8rem; opacity: 0.8;">Dias Rest.</div>
                        <div style="font-size: 1.2rem; font-weight: bold;">{int(resta_dias)}</div>
                    </div>
                </div>
                """
                st.markdown(html_metricas, unsafe_allow_html=True)
                
                if atual > 0:
                    st.warning(f"Fim previsto: {data_fim.strftime('%d/%m/%Y')}")
                else:
                    st.error("🚨 ESTOQUE ZERADO")
                
                if st.session_state.autenticado:
                    with st.expander("Ajustar / Comprar"):
                        v_add = st.number_input("Qtd Comprada", 0.0, key=f"add_{r['id']}")
                        v_pago = st.number_input("Valor R$", 0.0, key=f"v_{r['id']}")
                        if st.button("Salvar Ajuste", key=f"btn_{r['id']}", use_container_width=True):
                            requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, 
                                           json={"qtd_total": float(atual + v_add), "data_inicio": hoje.strftime('%Y-%m-%d')})
                            requests.post(f"{URL_BASE}compras", headers=HEADERS, 
                                           json={"nome_remedio": r['nome'], "valor": float(v_pago), "data_compra": hoje.strftime('%Y-%m-%d')})
                            enviar_telegram(f"✅ Compra: {r['nome']} (+{v_add} un) | R$ {v_pago:.2f}")
                            st.success("Registrado!"); st.cache_data.clear(); time.sleep(1.5); st.rerun()

elif aba == "Financeiro":
    st.subheader("💰 Gastos Mensais")
    df_com = buscar_dados("compras")
    df_con = buscar_dados("consultas")
    
    if not df_com.empty or not df_con.empty:
        if not df_com.empty: df_com['data'] = pd.to_datetime(df_com['data_compra'])
        if not df_con.empty: df_con['data'] = pd.to_datetime(df_con['data_consulta'])
        
        c1, c2 = st.columns(2)
        ano_sel = c1.selectbox("Ano", [2024, 2025, 2026], index=2)
        mes_sel = c2.selectbox("Mês", list(range(1, 13)), index=datetime.now().month - 1)
        
        f_com = df_com[(df_com['data'].dt.year == ano_sel) & (df_com['data'].dt.month == mes_sel)] if not df_com.empty else pd.DataFrame()
        f_con = df_con[(df_con['data'].dt.year == ano_sel) & (df_con['data'].dt.month == mes_sel)] if not df_con.empty else pd.DataFrame()
        
        tr, tc = f_com['valor'].sum() if not f_com.empty else 0, f_con['valor'].sum() if not f_con.empty else 0
        
        # Painel Financeiro usando HTML Flexível
        html_fin = f"""
        <div style="display: flex; justify-content: space-around; padding: 15px 0; margin-top: 15px; margin-bottom: 15px; border-radius: 8px; border: 1px solid rgba(128,128,128,0.2);">
            <div style="text-align: center; width: 50%; border-right: 1px solid rgba(128,128,128,0.2);">
                <div style="font-size: 0.9rem; opacity: 0.8;">💊 Remédios</div>
                <div style="font-size: 1.2rem; font-weight: bold;">R$ {tr:,.2f}</div>
            </div>
            <div style="text-align: center; width: 50%;">
                <div style="font-size: 0.9rem; opacity: 0.8;">🩺 Consultas</div>
                <div style="font-size: 1.2rem; font-weight: bold;">R$ {tc:,.2f}</div>
            </div>
        </div>
        """
        st.markdown(html_fin, unsafe_allow_html=True)
        
        with st.container(border=True):
            st.write("**INVESTIMENTO TOTAL**")
            st.title(f"R$ {tr + tc:,.2f}")
        
        if st.button("📥 Gerar Planilha CSV", use_container_width=True):
            relatorio = pd.concat([df_com, df_con], sort=False)
            csv = relatorio.to_csv(index=False).encode('utf-8')
            st.download_button(label="Baixar Relatório", data=csv, file_name=f"relatorio_saude_{ano_sel}_{mes_sel}.csv", mime="text/csv", use_container_width=True)

elif aba == "Consultas":
    st.subheader("🩺 Histórico")
    df = buscar_dados("consultas")
    if not df.empty:
        st.dataframe(df[['data_consulta', 'medico', 'valor']], hide_index=True, use_container_width=True)

elif aba == "Cadastrar":
    if st.session_state.autenticado:
        t = st.selectbox("O que cadastrar?", ["Remédio", "Consulta"])
        with st.form("cad_form"):
            if t == "Remédio":
                n = st.text_input("Nome")
                q = st.number_input("Qtd Inicial")
                d = st.number_input("Dose/Dia")
                p = st.number_input("Preço Inicial")
                if st.form_submit_button("SALVAR REMÉDIO", use_container_width=True):
                    requests.post(f"{URL_BASE}remedios", headers=HEADERS, json={"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "data_inicio": datetime.now().strftime('%Y-%m-%d')})
                    requests.post(f"{URL_BASE}compras", headers=HEADERS, json={"nome_remedio": n, "valor": float(p), "data_compra": datetime.now().strftime('%Y-%m-%d')})
                    enviar_telegram(f"🆕 Cadastrado: {n}")
                    st.success("Salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()
            else:
                m = st.text_input("Médico")
                v = st.number_input("Valor")
                if st.form_submit_button("SALVAR CONSULTA", use_container_width=True):
                    requests.post(f"{URL_BASE}consultas", headers=HEADERS, json={"medico": m, "valor": float(v), "data_consulta": datetime.now().strftime('%Y-%m-%d')})
                    st.success("Salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()

elif aba == "Remover":
    if st.session_state.autenticado:
        tab = st.selectbox("Onde deseja apagar?", ["remedios", "consultas", "compras"])
        df_del = buscar_dados(tab)
        if not df_del.empty:
            campo = 'nome' if tab == 'remedios' else ('nome_remedio' if tab == 'compras' else 'medico')
            it_selecionado = st.selectbox("Selecione o item:", df_del[campo].tolist())
            
            if st.button("🗑️ EXCLUIR DEFINITIVAMENTE", type="primary", use_container_width=True):
                id_item = df_del[df_del[campo] == it_selecionado]['id'].values[0]
                
                if tab == "remedios":
                    nome_rem = it_selecionado
                    requests.delete(f"{URL_BASE}remedios?id=eq.{id_item}", headers=HEADERS)
                    requests.delete(f"{URL_BASE}compras?nome_remedio=eq.{nome_rem}", headers=HEADERS)
                else:
                    requests.delete(f"{URL_BASE}{tab}?id=eq.{id_item}", headers=HEADERS)
                
                st.cache_data.clear()
                st.rerun()
    else:
        st.info("Acesse com a senha para remover dados.")
