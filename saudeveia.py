import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import time

# --- 1. CONFIGURAÇÕES ---
URL_SUPABASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
TOKEN_TELEGRAM = "8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM"
CHAT_ID = "5256921022"
SENHA_ADM = "1234"

HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. FUNÇÕES BASE ---
def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem}, timeout=5)
    except: pass

def api_get(tabela):
    try:
        res = requests.get(f"{URL_SUPABASE}{tabela}?select=*&order=id.desc", headers=HEADERS)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            for col in ['data_inicio', 'data_consulta', 'data_compra']:
                if not df.empty and col in df.columns:
                    df[col] = pd.to_datetime(df[col])
            return df
    except: pass
    return pd.DataFrame()

# --- 3. ESTILO CSS (FORÇANDO VISIBILIDADE TOTAL) ---
st.set_page_config(page_title="Saúde Família", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    /* FUNDO GERAL BRANCO */
    .stApp { background-color: #FFFFFF !important; }

    /* SIDEBAR AZUL CLARINHO */
    [data-testid="stSidebar"] {
        background-color: #E6F0FF !important;
        border-right: 1px solid #C2D6F0;
    }
    [data-testid="stSidebar"] * { color: #000000 !important; }

    /* FORÇAR TEXTO PRETO EM TUDO */
    .stApp, .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3 {
        color: #000000 !important;
    }

    /* CORREÇÃO DOS CARDS (PÁGINA DE HISTÓRICO E ESTOQUE) */
    .med-card {
        background-color: #F8F9FA !important;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #E2E8F0;
        border-left: 12px solid #3B82F6;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .med-card * {
        color: #000000 !important; /* Força tudo dentro do card a ser preto */
    }

    /* CORREÇÃO DO VALOR FINANCEIRO (METRIC) */
    [data-testid="stMetricValue"] {
        color: #000000 !important;
        font-weight: bold !important;
    }
    [data-testid="stMetricLabel"] {
        color: #444444 !important;
    }

    /* CAMPOS DE ENTRADA BRANCOS */
    input, .stTextInput div, .stNumberInput div, div[data-baseweb="input"], .stSelectbox div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    input {
        -webkit-text-fill-color: #000000 !important;
    }

    /* BOTÕES */
    div.stButton > button {
        background-color: #3B82F6 !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🏥 Gestão Saúde</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    if "admin" not in st.session_state: st.session_state.admin = False
    
    if not st.session_state.admin:
        st.markdown("### 🔒 Acesso")
        pw = st.text_input("Senha ADM", type="password")
        if st.button("Entrar no Modo ADM") or (pw == SENHA_ADM):
            if pw == SENHA_ADM:
                st.session_state.admin = True
                st.rerun()
            elif pw != "":
                st.error("Senha Incorreta")
    else:
        st.success("✅ Modo Editor Ativo")
        if st.button("Sair do Modo ADM"):
            st.session_state.admin = False
            st.rerun()
    
    st.markdown("---")
    menu = st.radio("Navegação", ["📊 Estoque", "🩺 Consultas", "💰 Financeiro", "➕ Cadastro", "🗑️ Remover"])

# --- 5. TELAS ---

if menu == "📊 Estoque":
    st.title("💊 Controle de Estoque")
    df = api_get("remedios")
    if df.empty:
        st.info("Nenhum remédio cadastrado.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            dias_passados = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_passados * r['dose_diaria'])))
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)
            
            st.markdown(f"""
                <div class="med-card">
                    <span style="font-size: 1.3em;"><b>{r['nome'].upper()}</b></span><br>
                    <p style="margin:0;">📦 Estoque: <b>{estoque_atual} un.</b> | 🕒 Dose: <b>{r['dose_diaria']} p/ dia</b></p>
                    <p style="margin-top:8px; font-size: 1.1em; color: {'#CC0000' if dias_restantes < 7 else '#166534'} !important;">
                        📅 Acaba em: <b>{data_fim.strftime('%d/%m/%Y')}</b>
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.admin:
                with st.expander(f"📥 Repor {r['nome']}"):
                    n_q = st.number_input("Qtd nova", min_value=1, value=30, key=f"q_{r['id']}")
                    n_v = st.number_input("Preço", value=float(r['preco']), key=f"v_{r['id']}")
                    if st.button("Confirmar Reposição", key=f"btn_{r['id']}"):
                        total = estoque_atual + n_q
                        requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(total), "data_inicio": str(hoje.date()), "preco": float(n_v)})
                        requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(n_v), "data_compra": str(hoje.date())})
                        st.success("Atualizado!"); time.sleep(1); st.rerun()

elif menu == "🩺 Consultas":
    st.title("🩺 Histórico de Consultas")
    df_c = api_get("consultas")
    if df_c.empty:
        st.info("Nenhuma consulta registrada.")
    else:
        for _, c in df_c.iterrows():
            st.markdown(f"""
                <div class="med-card" style="border-left-color: #10B981;">
                    <p style="margin:0;"><b>Data: {c['data_consulta'].strftime('%d/%m/%Y')}</b></p>
                    <p style="margin:0; font-size: 1.2em;"><b>Médico: {c['medico']}</b></p>
                    <p style="margin:0;"><b>Valor: R$ {float(c.get('valor', 0)):.2f}</b></p>
                </div>
            """, unsafe_allow_html=True)

elif menu == "💰 Financeiro":
    st.title("💰 Resumo Financeiro")
    df_r, df_c = api_get("compras"), api_get("consultas")
    t1 = df_r['valor'].sum() if not df_r.empty else 0
    t2 = df_c['valor'].sum() if not df_c.empty else 0
    
    st.metric("Total Gasto", f"R$ {t1+t2:.2f}")
    
    st.markdown("### 🛒 Detalhes de Compras")
    if not df_r.empty:
        # Tabela formatada
        st.dataframe(df_r[['data_compra', 'nome_remedio', 'valor']], use_container_width=True)

elif menu == "➕ Cadastro":
    if not st.session_state.admin: st.warning("🔒 Entre no modo ADM.")
    else:
        tipo = st.selectbox("Tipo:", ["Remédio", "Consulta"])
        with st.form("new_cad"):
            if tipo == "Remédio":
                n, q = st.text_input("Nome"), st.number_input("Qtd", value=30)
                d, p = st.number_input("Dose/dia", value=1.0), st.number_input("Preço", value=0.0)
                if st.form_submit_button("Salvar"):
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":n,"valor":float(p),"data_compra":str(datetime.now().date())})
                    st.success("OK!"); time.sleep(1); st.rerun()
            else:
                m, v, dt = st.text_input("Médico"), st.number_input("Valor"), st.date_input("Data")
                if st.form_submit_button("Salvar"):
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    st.success("OK!"); time.sleep(1); st.rerun()

elif menu == "🗑️ Remover":
    if not st.session_state.admin: st.warning("🔒 Entre no modo ADM.")
    else:
        tab = st.selectbox("Categoria:", ["remedios", "consultas", "compras"])
        df_d = api_get(tab)
        if not df_d.empty:
            col = 'nome' if tab == 'remedios' else 'medico' if tab == 'consultas' else 'nome_remedio'
            it = st.selectbox("Item:", df_d[col].tolist())
            if st.button("Remover"):
                requests.delete(f"{URL_SUPABASE}{tab}?id=eq.{df_d[df_d[col] == it]['id'].values[0]}", headers=HEADERS)
                st.rerun()
