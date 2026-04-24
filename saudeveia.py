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

# --- 3. ESTILO CSS (LIMPEZA TOTAL DOS CAMPOS ESCUROS) ---
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

    /* FORÇAR CAMPOS DE ENTRADA BRANCOS */
    /* Isso remove o fundo escuro que aparece na sua imagem */
    div[data-testid="stForm"] { background-color: #FFFFFF !important; border: none !important; }
    
    input, .stTextInput div, .stNumberInput div, div[data-baseweb="input"], .stSelectbox div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-color: #3B82F6 !important;
    }
    
    /* Cor do texto dentro dos inputs */
    input {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* Labels e títulos sempre pretos */
    label, .stMarkdown p, h1, h2, h3 {
        color: #000000 !important;
        font-weight: bold !important;
    }

    /* CARD DOS REMÉDIOS */
    .med-card {
        background-color: #F8F9FA !important;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #E2E8F0;
        border-left: 12px solid #3B82F6;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }

    /* BOTÕES AZUIS COM LETRA BRANCA */
    div.stButton > button {
        background-color: #3B82F6 !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 8px !important;
        height: 3em !important;
    }
    
    div.stButton > button:hover {
        background-color: #2563EB !important;
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
        st.markdown("### 🔒 Área Restrita")
        pw = st.text_input("Senha ADM", type="password")
        # Botão físico para ajudar no celular
        if st.button("Entrar no Modo ADM") or (pw == SENHA_ADM):
            if pw == SENHA_ADM:
                st.session_state.admin = True
                st.rerun()
            elif pw != "":
                st.error("Senha Incorreta")
    else:
        st.success("✅ Você é Administrador")
        if st.button("Sair do Modo ADM"):
            st.session_state.admin = False
            st.rerun()
    
    st.markdown("---")
    menu = st.radio("Navegação", ["📊 Estoque", "🩺 Consultas", "💰 Financeiro", "➕ Cadastro", "🗑️ Remover"])

# --- 5. LÓGICA DAS TELAS ---
if menu == "📊 Estoque":
    st.title("💊 Controle de Remédios")
    df = api_get("remedios")
    if df.empty:
        st.info("Nenhum remédio cadastrado.")
    else:
        hoje = datetime.now()
        if "alertas_enviados" not in st.session_state: st.session_state.alertas_enviados = []

        for _, r in df.iterrows():
            dias_passados = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_passados * r['dose_diaria'])))
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)
            
            st.markdown(f"""
                <div class="med-card">
                    <span style="font-size: 1.3em; color: black;"><b>{r['nome'].upper()}</b></span><br>
                    <p style="margin:0; color: #444;">📦 Estoque: <b>{estoque_atual} un.</b> | 🕒 Dose: <b>{r['dose_diaria']} p/ dia</b></p>
                    <p style="margin-top:8px; font-size: 1.1em; color: {'#CC0000' if dias_restantes < 7 else '#166534'} !important;">
                        📅 Acaba em: <b>{data_fim.strftime('%d/%m/%Y')}</b> ({dias_restantes} dias)
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.admin:
                with st.expander(f"📥 Repor {r['nome']}"):
                    # Chaves únicas para evitar conflito de IDs no Streamlit
                    n_q = st.number_input("Quantidade nova", min_value=1, value=30, key=f"q_{r['id']}")
                    n_v = st.number_input("Preço da caixa (R$)", value=float(r['preco']), key=f"v_{r['id']}")
                    if st.button("Confirmar Reposição", key=f"btn_{r['id']}"):
                        total = estoque_atual + n_q
                        requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(total), "data_inicio": str(hoje.date()), "preco": float(n_v)})
                        requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(n_v), "data_compra": str(hoje.date())})
                        st.success("Estoque atualizado!"); time.sleep(1); st.cache_data.clear(); st.rerun()

elif menu == "🩺 Consultas":
    st.title("🩺 Histórico")
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            st.markdown(f"""<div class="med-card"><b>{c['data_consulta'].strftime('%d/%m/%Y')}</b> - Dr. {c['medico']}<br>R$ {float(c.get('valor', 0)):.2f}</div>""", unsafe_allow_html=True)

elif menu == "💰 Financeiro":
    st.title("💰 Financeiro")
    df_r, df_c = api_get("compras"), api_get("consultas")
    t1 = df_r['valor'].sum() if not df_r.empty else 0
    t2 = df_c['valor'].sum() if not df_c.empty else 0
    st.metric("Total Gasto", f"R$ {t1+t2:.2f}")
    if not df_r.empty: st.dataframe(df_r[['data_compra', 'nome_remedio', 'valor']], use_container_width=True)

elif menu == "➕ Cadastro":
    if not st.session_state.admin: st.warning("🔒 Entre no modo ADM para cadastrar.")
    else:
        tipo = st.selectbox("O que deseja cadastrar?", ["Remédio", "Consulta"])
        with st.form("form_cadastro"):
            if tipo == "Remédio":
                n = st.text_input("Nome do Remédio")
                q = st.number_input("Qtd Inicial", value=30)
                d = st.number_input("Dose Diária", value=1.0)
                p = st.number_input("Preço", value=0.0)
                if st.form_submit_button("Salvar Medicamento"):
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":n,"valor":float(p),"data_compra":str(datetime.now().date())})
                    st.success("Cadastrado!"); time.sleep(1); st.rerun()
            else:
                m = st.text_input("Nome do Médico")
                v = st.number_input("Valor", value=0.0)
                dt = st.date_input("Data da Consulta")
                if st.form_submit_button("Salvar Consulta"):
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    st.success("Salvo!"); time.sleep(1); st.rerun()

elif menu == "🗑️ Remover":
    if not st.session_state.admin: st.warning("🔒 Entre no modo ADM para remover.")
    else:
        tab = st.selectbox("Escolha a categoria:", ["remedios", "consultas", "compras"])
        df_d = api_get(tab)
        if not df_d.empty:
            col = 'nome' if tab == 'remedios' else 'medico' if tab == 'consultas' else 'nome_remedio'
            it = st.selectbox("Item a ser excluído:", df_d[col].tolist())
            if st.button("Remover Permanentemente"):
                requests.delete(f"{URL_SUPABASE}{tab}?id=eq.{df_d[df_d[col] == it]['id'].values[0]}", headers=HEADERS)
                st.rerun()
