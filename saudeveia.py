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
HEADERS = {"apikey": API_KEY, "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}

def enviar_telegram(msg):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", data={"chat_id": CHAT_ID, "text": msg}, timeout=5)
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

# --- 2. DESIGN ULTRA-COMPACTO (CSS) ---
st.set_page_config(page_title="Saúde", page_icon="💊", layout="wide")

st.markdown("""
    <style>
    /* Reduzir o cabeçalho e espaços do Streamlit */
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    header { visibility: hidden; }
    
    /* Fontes menores e compactas para o celular */
    html, body, [class*="css"] { font-size: 0.9rem !important; }
    
    /* Estilo das métricas (Deixar os números menores) */
    [data-testid="stMetricValue"] { font-size: 1rem !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { font-size: 0.7rem !important; }
    
    /* Diminuir a altura dos containers */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0.4rem !important;
        margin-bottom: -1rem !important;
    }
    
    /* Deixar botões menores */
    .stButton button { padding: 0.2rem 0.5rem !important; font-size: 0.8rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. NOTIFICAÇÕES INTELIGENTES ---
if "notificou_entrada" not in st.session_state:
    enviar_telegram("🔌 App Acessado")
    st.session_state.notificou_entrada = True

# --- 4. MENU LATERAL ---
with st.sidebar:
    st.title("🏥 Saúde")
    if "admin" not in st.session_state: st.session_state.admin = False
    if not st.session_state.admin:
        pw = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if pw == "1234": st.session_state.admin = True; st.rerun()
    else:
        if st.button("Sair"): st.session_state.admin = False; st.rerun()
    aba = st.radio("Menu", ["📦 Estoque", "💰 Gastos", "🩺 Consultas", "➕ Novo", "🗑️ Apagar"])

meses_pt = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}

# --- 5. TELA DE ESTOQUE (OTIMIZADA) ---
if aba == "📦 Estoque":
    df = api_get("remedios")
    if not df.empty:
        hoje = datetime.now()
        itens_criticos = []

        for _, r in df.iterrows():
            dias_p = (hoje - r['data_inicio']).days
            estoque = max(0, int(r['qtd_total'] - (dias_p * r['dose_diaria'])))
            dias_r = int(estoque / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_f = hoje + timedelta(days=dias_r)
            
            if dias_r < 7: itens_criticos.append(f"- {r['nome']}")

            with st.container(border=True):
                # Título e Status na mesma linha
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{r['nome'].upper()}**")
                
                # Badges de status curtas
                if dias_r < 7: c2.error("REPOR")
                elif dias_r < 15: c2.warning("ALERTA")
                else: c2.success("OK")

                # Métricas lado a lado (Streamlit empilha no celular se faltar espaço)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Qtd", f"{estoque}")
                m2.metric("Dose", f"{r['dose_diaria']}")
                m3.metric("Restam", f"{dias_r}d")
                m4.metric("Fim", f"{data_f.day}/{meses_pt[data_f.month]}")

                if st.session_state.admin:
                    with st.expander("Ajustar"):
                        col_q, col_p = st.columns(2)
                        nq = col_q.number_input("Add Qtd", 1, 500, 30, key=f"q_{r['id']}")
                        np = col_p.number_input("Preço R$", 0.0, 5000.0, float(r['preco']), key=f"p_{r['id']}")
                        if st.button("Salvar", key=f"b_{r['id']}"):
                            requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(estoque + nq), "data_inicio": str(hoje.date()), "preco": float(np)})
                            requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":r['nome'], "valor":float(np), "data_compra":str(hoje.date())})
                            enviar_telegram(f"✅ Reposição: {r['nome']}")
                            st.rerun()

        # Notificação de estoque baixo (Uma vez por acesso)
        if itens_criticos and "notificou_estoque" not in st.session_state:
            enviar_telegram(f"⚠️ Alerta Estoque:\n" + "\n".join(itens_criticos))
            st.session_state.notificou_estoque = True

# --- TELAS SECUNDÁRIAS COMPACTADAS ---
elif aba == "💰 Gastos":
    df_f = api_get("compras")
    if not df_f.empty:
        st.metric("Total Gasto", f"R$ {df_f['valor'].sum():.2f}")
        st.dataframe(df_f[['data_compra', 'nome_remedio', 'valor']], use_container_width=True, hide_index=True)

elif aba == "🩺 Consultas":
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            with st.container(border=True):
                st.write(f"**{c['medico']}** | R$ {c['valor']:.2f} | {c['data_consulta'].strftime('%d/%m/%Y')}")

elif aba == "➕ Novo":
    if st.session_state.admin:
        with st.form("c"):
            n = st.text_input("Nome")
            c1, c2, c3 = st.columns(3)
            q = c1.number_input("Qtd", 1)
            d = c2.number_input("Dose", 0.1, 10.0, 1.0)
            p = c3.number_input("Preço", 0.0)
            if st.form_submit_button("Cadastrar"):
                requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":n,"valor":float(p),"data_compra":str(datetime.now().date())})
                st.rerun()
    else: st.warning("Login necessário.")

elif aba == "🗑️ Apagar":
    if st.session_state.admin:
        df_d = api_get("remedios")
        if not df_d.empty:
            it = st.selectbox("Item", df_d['nome'].tolist())
            if st.button("Excluir"):
                id_d = df_d[df_d['nome'] == it]['id'].values[0]
                requests.delete(f"{URL_SUPABASE}remedios?id=eq.{id_d}", headers=HEADERS)
                st.rerun()
