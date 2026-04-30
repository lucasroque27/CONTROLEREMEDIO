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

# --- 2. INTERFACE E AJUSTES DE TELA ---
st.set_page_config(page_title="Saúde Rock", layout="centered")

# CSS para evitar cortes e ajustar fontes
st.markdown("""
    <style>
    /* Resolve o problema de cortar o topo */
    .stApp { margin-top: -50px; }
    .block-container { padding-top: 2rem !important; }
    
    /* Botões ocupando a largura toda para facilitar o toque */
    .stButton button { width: 100%; }
    
    /* Ajuste fino para métricas não ficarem gigantes no celular */
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
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
        if st.button("Sair do Modo ADM"):
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
                
                # Usando colunas nativas (mais estável)
                c1, c2, c3 = st.columns(3)
                c1.metric("Estoque", f"{atual:g}")
                c2.metric("Dose", f"{dose:g}")
                c3.metric("Dias", int(resta_dias))
                
                if atual > 0:
                    st.info(f"📅 Término: {data_fim.strftime('%d/%m/%Y')}")
                else:
                    st.error("🚨 ESTOQUE ZERADO")
                
                if st.session_state.autenticado:
                    with st.expander("Ajustar / Comprar"):
                        v_add = st.number_input("Qtd Comprada", 0.0, key=f"add_{r['id']}")
                        v_pago = st.number_input("Valor R$", 0.0, key=f"v_{r['id']}")
                        if st.button("Salvar Ajuste", key=f"btn_{r['id']}"):
                            requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, 
                                           json={"qtd_total": float(atual + v_add), "data_inicio": hoje.strftime('%Y-%m-%d')})
                            requests.post(f"{URL_BASE}compras", headers=HEADERS, 
                                           json={"nome_remedio": r['nome'], "valor": float(v_pago), "data_compra": hoje.strftime('%Y-%m-%d')})
                            enviar_telegram(f"✅ Compra: {r['nome']} (+{v_add} un) | R$ {v_pago:.2f}")
                            st.success("Salvo!"); st.cache_data.clear(); time.sleep(1.5); st.rerun()

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
        
        # Layout financeiro limpo
        with st.container(border=True):
            col_a, col_b = st.columns(2)
            col_a.metric("💊 Remédios", f"R$ {tr:,.2f}")
            col_b.metric("🩺 Consultas", f"R$ {tc:,.2f}")
            st.divider()
            st.write("**TOTAL INVESTIDO**")
            st.subheader(f"R$ {tr + tc:,.2f}")
        
        if st.button("📥 Gerar Planilha CSV"):
            relatorio = pd.concat([df_com, df_con], sort=False)
            csv = relatorio.to_csv(index=False).encode('utf-8')
            st.download_button(label="Baixar Relatório", data=csv, file_name=f"financeiro_{ano_sel}_{mes_sel}.csv", mime="text/csv")

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
                if st.form_submit_button("SALVAR"):
                    requests.post(f"{URL_BASE}remedios", headers=HEADERS, json={"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "data_inicio": datetime.now().strftime('%Y-%m-%d')})
                    requests.post(f"{URL_BASE}compras", headers=HEADERS, json={"nome_remedio": n, "valor": float(p), "data_compra": datetime.now().strftime('%Y-%m-%d')})
                    enviar_telegram(f"🆕 Cadastrado: {n}")
                    st.success("Sucesso!"); st.cache_data.clear(); time.sleep(1); st.rerun()
            else:
                m = st.text_input("Médico")
                v = st.number_input("Valor")
                if st.form_submit_button("SALVAR"):
                    requests.post(f"{URL_BASE}consultas", headers=HEADERS, json={"medico": m, "valor": float(v), "data_consulta": datetime.now().strftime('%Y-%m-%d')})
                    st.success("Sucesso!"); st.cache_data.clear(); time.sleep(1); st.rerun()

elif aba == "Remover":
    if st.session_state.autenticado:
        tab = st.selectbox("Tabela", ["remedios", "consultas", "compras"])
        df_del = buscar_dados(tab)
        if not df_del.empty:
            campo = 'nome' if tab == 'remedios' else ('nome_remedio' if tab == 'compras' else 'medico')
            it = st.selectbox("Item:", df_del[campo].tolist())
            if st.button("🗑️ EXCLUIR", type="primary"):
                id_item = df_del[df_del[campo] == it]['id'].values[0]
                if tab == "remedios":
                    requests.delete(f"{URL_BASE}remedios?id=eq.{id_item}", headers=HEADERS)
                    requests.delete(f"{URL_BASE}compras?nome_remedio=eq.{it}", headers=HEADERS)
                else:
                    requests.delete(f"{URL_BASE}{tab}?id=eq.{id_item}", headers=HEADERS)
                st.cache_data.clear(); st.rerun()
