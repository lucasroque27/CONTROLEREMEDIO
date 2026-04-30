import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time

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

# --- 2. INTERFACE E CSS ANTI-CORTE ---
st.set_page_config(page_title="Saúde Rock", layout="centered")

st.markdown("""
    <style>
    .stApp { margin-top: 0px !important; }
    .block-container { 
        padding-top: 3.5rem !important; 
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; }
    .flex-grid { display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between; margin-bottom: 10px; }
    .flex-item { flex: 1 1 100px; min-width: 85px; text-align: center; background: rgba(128, 128, 128, 0.05); padding: 10px; border-radius: 8px; }
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    [data-testid="stWidgetLabel"] p { margin-bottom: 8px !important; font-size: 1rem !important; }
    </style>
""", unsafe_allow_html=True)

if "autenticado" not in st.session_state: 
    st.session_state.autenticado = False

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Controle")
    if not st.session_state.autenticado:
        senha = st.text_input("Senha ADM", type="password")
        if st.button("Entrar") or (senha == "1234"):
            if senha == "1234":
                st.session_state.autenticado = True
                st.rerun()
    else:
        if st.button("Sair do ADM"):
            st.session_state.autenticado = False
            st.rerun()
    
    st.divider()
    aba = st.radio("Navegação", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"])

# --- 4. TELAS ---

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
            
            # Alerta automático Telegram para estoque baixo
            if resta_dias <= 5 and f"alerta_{r['id']}" not in st.session_state:
                enviar_telegram(f"⚠️ ESTOQUE BAIXO: {r['nome'].upper()} acaba em {int(resta_dias)} dias!")
                st.session_state[f"alerta_{r['id']}"] = True

            with st.container(border=True):
                st.markdown(f"**💊 {r['nome'].upper()}**")
                st.markdown(f"""
                <div class="flex-grid">
                    <div class="flex-item">
                        <div style="font-size:0.7rem; opacity:0.7;">Estoque</div>
                        <div style="font-size:1.1rem; font-weight:bold;">{atual:g}</div>
                    </div>
                    <div class="flex-item">
                        <div style="font-size:0.7rem; opacity:0.7;">Dose/Dia</div>
                        <div style="font-size:1.1rem; font-weight:bold;">{dose:g}</div>
                    </div>
                    <div class="flex-item">
                        <div style="font-size:0.7rem; opacity:0.7;">Dias Rest.</div>
                        <div style="font-size:1.1rem; font-weight:bold;">{int(resta_dias)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if resta_dias > 0:
                    st.caption(f"📅 Fim previsto: {data_fim.strftime('%d/%m/%Y')}")
                else:
                    st.error("🚨 ESTOQUE ZERADO")
                
                if st.session_state.autenticado:
                    with st.expander("Ajustar / Comprar"):
                        v_add = st.number_input("Qtd Adquirida", 0.0, key=f"add_{r['id']}")
                        v_pago = st.number_input("Valor Pago R$", 0.0, key=f"v_{r['id']}")
                        if st.button("Salvar Ajuste", key=f"btn_{r['id']}"):
                            novo_total = atual + v_add
                            requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, 
                                           json={"qtd_total": float(novo_total), "data_inicio": hoje.strftime('%Y-%m-%d')})
                            if v_pago > 0:
                                requests.post(f"{URL_BASE}compras", headers=HEADERS, 
                                               json={"nome_remedio": r['nome'], "valor": float(v_pago), "data_compra": hoje.strftime('%Y-%m-%d')})
                            if f"alerta_{r['id']}" in st.session_state: del st.session_state[f"alerta_{r['id']}"]
                            enviar_telegram(f"✅ Atualizado: {r['nome']} | Total: {novo_total}")
                            st.success("Atualizado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

elif aba == "Financeiro":
    st.subheader("💰 Gastos Mensais")
    df_com = buscar_dados("compras")
    df_con = buscar_dados("consultas")
    
    col_sel1, col_sel2 = st.columns(2)
    ano_sel = col_sel1.selectbox("Ano", [2025, 2026], index=1)
    mes_sel = col_sel2.selectbox("Mês", list(range(1, 13)), index=datetime.now().month - 1)
    
    tr, tc = 0.0, 0.0
    if not df_com.empty:
        df_com['data'] = pd.to_datetime(df_com['data_compra'])
        tr = df_com[(df_com['data'].dt.year == ano_sel) & (df_com['data'].dt.month == mes_sel)]['valor'].sum()
    if not df_con.empty:
        df_con['data'] = pd.to_datetime(df_con['data_consulta'])
        tc = df_con[(df_con['data'].dt.year == ano_sel) & (df_con['data'].dt.month == mes_sel)]['valor'].sum()
    
    with st.container(border=True):
        st.markdown(f"""
        <div class="flex-grid">
            <div class="flex-item">
                <div style="font-size:0.8rem; opacity:0.7;">💊 Remédios</div>
                <div style="font-size:1.2rem; font-weight:bold;">R$ {tr:,.2f}</div>
            </div>
            <div class="flex-item">
                <div style="font-size:0.8rem; opacity:0.7;">🩺 Consultas</div>
                <div style="font-size:1.2rem; font-weight:bold;">R$ {tc:,.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        st.write("**TOTAL INVESTIDO**")
        st.title(f"R$ {tr + tc:,.2f}")
    
    if st.button("📥 Baixar Relatório CSV"):
        rel = pd.concat([df_com, df_con], sort=False)
        st.download_button("Clique aqui para baixar", rel.to_csv(index=False).encode('utf-8'), "financeiro.csv", "text/csv")

elif aba == "Consultas":
    st.subheader("🩺 Histórico")
    df = buscar_dados("consultas")
    if not df.empty:
        st.dataframe(df.sort_values('data_consulta', ascending=False), hide_index=True, use_container_width=True)

elif aba == "Cadastrar":
    if st.session_state.autenticado:
        st.subheader("📝 Novo Cadastro")
        st.write("") 
        modo = st.radio("Selecione o tipo:", ["Remédio", "Consulta"])
        
        with st.form("cad_form"):
            if modo == "Remédio":
                n = st.text_input("Nome do Remédio")
                q = st.number_input("Quantidade em Estoque", 0.0)
                d = st.number_input("Dose Diária", 0.0)
                p = st.number_input("Preço da Compra (R$)", 0.0)
                if st.form_submit_button("Salvar Cadastro"):
                    hoje_str = datetime.now().strftime('%Y-%m-%d')
                    requests.post(f"{URL_BASE}remedios", headers=HEADERS, json={"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "data_inicio": hoje_str})
                    if p > 0:
                        requests.post(f"{URL_BASE}compras", headers=HEADERS, json={"nome_remedio": n, "valor": float(p), "data_compra": hoje_str})
                    st.success("Remédio e Gasto Registrados!"); st.cache_data.clear(); time.sleep(1); st.rerun()
            else:
                md = st.text_input("Médico / Especialidade")
                vl = st.number_input("Valor da Consulta", 0.0)
                if st.form_submit_button("Salvar Cadastro"):
                    requests.post(f"{URL_BASE}consultas", headers=HEADERS, json={"medico": md, "valor": float(vl), "data_consulta": datetime.now().strftime('%Y-%m-%d')})
                    st.success("Consulta Registrada!"); st.cache_data.clear(); time.sleep(1); st.rerun()
    else:
        st.warning("⚠️ Acesse o modo ADM no menu lateral para cadastrar dados.")

elif aba == "Remover":
    if st.session_state.autenticado:
        t = st.selectbox("Tabela para remoção", ["remedios", "consultas", "compras"])
        df_del = buscar_dados(t)
        if not df_del.empty:
            c = 'nome' if t == 'remedios' else ('nome_remedio' if t == 'compras' else 'medico')
            it = st.selectbox("Item para excluir permanentemente:", df_del[c].tolist())
            if st.button("🗑️ APAGAR AGORA", type="primary"):
                id_it = df_del[df_del[c] == it]['id'].values[0]
                requests.delete(f"{URL_BASE}{t}?id=eq.{id_it}", headers=HEADERS)
                st.success("Removido com sucesso!"); st.cache_data.clear(); time.sleep(1); st.rerun()
