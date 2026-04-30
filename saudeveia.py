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

# --- 2. INTERFACE ---
st.set_page_config(page_title="Saúde Rock", layout="centered")

st.markdown("""
    <style>
    .stApp { margin-top: 0px !important; }
    .block-container { padding-top: 2rem !important; }
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
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
            
            # --- ALERTA AUTOMÁTICO TELEGRAM ---
            # Se restarem menos de 5 dias, envia aviso (uma vez por sessão para não spammar)
            if resta_dias <= 5 and f"alerta_{r['id']}" not in st.session_state:
                msg_alerta = f"⚠️ ALERTA DE ESTOQUE: O remédio {r['nome'].upper()} dura apenas mais {int(resta_dias)} dias! (Fim previsto: {data_fim.strftime('%d/%m')})"
                enviar_telegram(msg_alerta)
                st.session_state[f"alerta_{r['id']}"] = True # Marca que já avisou nesta sessão

            with st.container(border=True):
                st.markdown(f"**💊 {r['nome'].upper()}**")
                c1, c2, c3 = st.columns(3)
                c1.metric("Estoque", f"{atual:g}")
                c2.metric("Dose/Dia", f"{dose:g}")
                c3.metric("Dias", int(resta_dias))
                
                if resta_dias > 5:
                    st.success(f"📅 Fim previsto: {data_fim.strftime('%d/%m/%Y')}")
                elif resta_dias > 0:
                    st.warning(f"⚠️ Acabando: {data_fim.strftime('%d/%m/%Y')}")
                else:
                    st.error("🚨 ESTOQUE ZERADO")
                
                if st.session_state.autenticado:
                    with st.expander("Ajustar Estoque / Registrar Compra"):
                        v_add = st.number_input("Qtd Comprada", 0.0, key=f"add_{r['id']}")
                        v_pago = st.number_input("Valor Pago R$", 0.0, key=f"v_{r['id']}")
                        if st.button("Salvar Alterações", key=f"btn_{r['id']}"):
                            novo_total = atual + v_add
                            requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, 
                                           json={"qtd_total": float(novo_total), "data_inicio": hoje.strftime('%Y-%m-%d')})
                            if v_pago > 0:
                                requests.post(f"{URL_BASE}compras", headers=HEADERS, 
                                               json={"nome_remedio": r['nome'], "valor": float(v_pago), "data_compra": hoje.strftime('%Y-%m-%d')})
                            
                            # Limpa o estado de alerta para poder avisar novamente no futuro
                            if f"alerta_{r['id']}" in st.session_state: del st.session_state[f"alerta_{r['id']}"]
                            
                            enviar_telegram(f"✅ Atualizado: {r['nome']} | Novo Estoque: {novo_total}")
                            st.success("Atualizado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

elif aba == "Financeiro":
    st.subheader("💰 Gestão de Gastos")
    df_com = buscar_dados("compras")
    df_con = buscar_dados("consultas")
    
    c1, c2 = st.columns(2)
    ano_sel = c1.selectbox("Ano", [2025, 2026], index=1)
    mes_sel = c2.selectbox("Mês", list(range(1, 13)), index=datetime.now().month - 1)
    
    tr, tc = 0.0, 0.0
    if not df_com.empty:
        df_com['data'] = pd.to_datetime(df_com['data_compra'])
        tr = df_com[(df_com['data'].dt.year == ano_sel) & (df_com['data'].dt.month == mes_sel)]['valor'].sum()
    if not df_con.empty:
        df_con['data'] = pd.to_datetime(df_con['data_consulta'])
        tc = df_con[(df_con['data'].dt.year == ano_sel) & (df_con['data'].dt.month == mes_sel)]['valor'].sum()
    
    with st.container(border=True):
        ca, cb = st.columns(2)
        ca.metric("Remédios", f"R$ {tr:,.2f}")
        cb.metric("Consultas", f"R$ {tc:,.2f}")
        st.divider()
        st.title(f"R$ {tr + tc:,.2f}")
    
    if st.button("📥 Baixar Relatório CSV"):
        rel = pd.concat([df_com, df_con], sort=False)
        st.download_button("Clique para baixar", rel.to_csv(index=False).encode('utf-8'), "relatorio.csv", "text/csv")

elif aba == "Consultas":
    st.subheader("🩺 Histórico")
    df = buscar_dados("consultas")
    if not df.empty:
        st.dataframe(df.sort_values('data_consulta', ascending=False), hide_index=True, use_container_width=True)

elif aba == "Cadastrar":
    if st.session_state.autenticado:
        modo = st.radio("Tipo:", ["Remédio", "Consulta"])
        with st.form("f_cad"):
            if modo == "Remédio":
                n = st.text_input("Nome")
                q = st.number_input("Qtd", 0.0)
                d = st.number_input("Dose/Dia", 0.0)
                if st.form_submit_button("Cadastrar"):
                    requests.post(f"{URL_BASE}remedios", headers=HEADERS, json={"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "data_inicio": datetime.now().strftime('%Y-%m-%d')})
                    st.success("Cadastrado!"); st.cache_data.clear(); time.sleep(1); st.rerun()
            else:
                m = st.text_input("Médico")
                v = st.number_input("Valor", 0.0)
                if st.form_submit_button("Cadastrar"):
                    requests.post(f"{URL_BASE}consultas", headers=HEADERS, json={"medico": m, "valor": float(v), "data_consulta": datetime.now().strftime('%Y-%m-%d')})
                    st.success("Cadastrado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

elif aba == "Remover":
    if st.session_state.autenticado:
        t = st.selectbox("Tabela", ["remedios", "consultas", "compras"])
        df_del = buscar_dados(t)
        if not df_del.empty:
            campo = 'nome' if t == 'remedios' else ('nome_remedio' if t == 'compras' else 'medico')
            item = st.selectbox("Item", df_del[campo].tolist())
            if st.button("EXCLUIR PERMANENTE"):
                id_item = df_del[df_del[campo] == item]['id'].values[0]
                requests.delete(f"{URL_BASE}{t}?id=eq.{id_item}", headers=HEADERS)
                st.success("Excluído!"); st.cache_data.clear(); time.sleep(1); st.rerun()
