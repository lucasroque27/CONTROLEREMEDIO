import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

# --- 1. CONFIGURAÇÕES ---
URL_SUPABASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
TOKEN_TELEGRAM = "8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM"
CHAT_ID = "5256921022"
HEADERS = {"apikey": API_KEY, "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}

def enviar_telegram(msg):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", data={"chat_id": CHAT_ID, "text": msg}, timeout=2)
    except: pass

def api_get(tabela):
    try:
        res = requests.get(f"{URL_SUPABASE}{tabela}?select=*&order=id.desc", headers=HEADERS)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            for col in ['data_inicio', 'data_consulta', 'data_compra']:
                if not df.empty and col in df.columns: df[col] = pd.to_datetime(df[col])
            return df
    except: pass
    return pd.DataFrame()

# --- 2. CSS ULTRA COMPACTO (A MÁGICA ESTÁ AQUI) ---
st.set_page_config(page_title="Saúde", page_icon="💊", layout="wide")

st.markdown("""
    <style>
    /* Remove espaços inúteis do topo */
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; max-width: 95% !important; }
    
    /* Diminui drasticamente o tamanho dos cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0.2rem 0.6rem !important;
        margin-bottom: -0.8rem !important;
        border-radius: 8px !important;
    }

    /* Ajusta as métricas para ficarem pequenas e em uma linha */
    [data-testid="stMetricValue"] { font-size: 0.95rem !important; font-weight: bold !important; color: #1E1E1E !important; }
    [data-testid="stMetricLabel"] { font-size: 0.65rem !important; margin-bottom: -5px !important; }
    [data-testid="stMetric"] { padding: 0px !important; }

    /* Estilo para o título do remédio */
    .remedio-titulo { font-size: 0.85rem !important; font-weight: 700; color: #333; margin: 0; }
    
    /* Diminuir altura de inputs e botões */
    .stNumberInput input { height: 30px !important; font-size: 0.8rem !important; }
    button { height: 28px !important; padding: 0px 10px !important; font-size: 0.75rem !important; }
    
    /* Esconde elementos desnecessários */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGICA DE ALERTAS ---
if "avisou_entrada" not in st.session_state:
    enviar_telegram("🔌 App aberto")
    st.session_state.avisou_entrada = True

# --- 4. INTERFACE ---
with st.sidebar:
    st.caption("💊 Gestão de Saúde")
    if "admin" not in st.session_state: st.session_state.admin = False
    if not st.session_state.admin:
        if st.text_input("Senha", type="password") == "1234": 
            st.session_state.admin = True
            st.rerun()
    aba = st.radio("Ir para:", ["Estoque", "Financeiro", "Adicionar"], label_visibility="collapsed")

if aba == "Estoque":
    df = api_get("remedios")
    if not df.empty:
        hoje = datetime.now()
        alertas = []
        
        for _, r in df.iterrows():
            dias_p = (hoje - r['data_inicio']).days
            estoque = max(0, int(r['qtd_total'] - (dias_p * r['dose_diaria'])))
            dias_r = int(estoque / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_f = hoje + timedelta(days=dias_r)
            
            if dias_r < 7: alertas.append(r['nome'])

            with st.container(border=True):
                # Linha de cima: Nome e Status
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"<p class='remedio-titulo'>💊 {r['nome'].upper()}</p>", unsafe_allow_html=True)
                
                if dias_r < 7: c2.caption("🔴 REPOR")
                elif dias_r < 15: c2.caption("🟡 ALERTA")
                else: c2.caption("🟢 OK")

                # Linha de baixo: Métricas compactas
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Qtd", f"{estoque}")
                m2.metric("Dose", f"{r['dose_diaria']}")
                m3.metric("Dias", f"{dias_r}d")
                m4.metric("Fim", f"{data_f.strftime('%d/%m')}")

                if st.session_state.admin:
                    with st.expander("Repor"):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        nq = col1.number_input("+ Qtd", 1, 500, 30, key=f"q_{r['id']}")
                        np = col2.number_input("R$", 0.0, 5000.0, float(r['preco']), key=f"p_{r['id']}")
                        if col3.button("✔", key=f"b_{r['id']}"):
                            requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(estoque + nq), "data_inicio": str(hoje.date()), "preco": float(np)})
                            requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":r['nome'], "valor":float(np), "data_compra":str(hoje.date())})
                            enviar_telegram(f"✅ Reposto: {r['nome']}")
                            st.rerun()

        if alertas and "avisou_estoque" not in st.session_state:
            enviar_telegram(f"⚠️ Acabando: {', '.join(alertas)}")
            st.session_state.avisou_estoque = True

# --- TELAS RESUMIDAS ---
elif aba == "Financeiro":
    df_f = api_get("compras")
    if not df_f.empty:
        st.metric("Gasto Total", f"R$ {df_f['valor'].sum():.2f}")
        st.dataframe(df_f[['data_compra', 'nome_remedio', 'valor']], use_container_width=True, hide_index=True)

elif aba == "Adicionar":
    if st.session_state.admin:
        with st.form("novo"):
            n = st.text_input("Nome")
            q = st.number_input("Qtd Inicial", 1)
            d = st.number_input("Dose Diária", 0.1, 10.0, 1.0)
            if st.form_submit_button("Salvar"):
                requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":0.0,"data_inicio":str(datetime.now().date())})
                st.rerun()
