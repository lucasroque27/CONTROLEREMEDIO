import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import time

# --- 1. CONFIGURAÇÕES (PRESERVADAS) ---
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

# --- 3. ESTILO CSS "ANTI-DARK MODE" (FOCO EM VISIBILIDADE) ---
st.set_page_config(page_title="Saúde Família", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    /* Forçar cores de texto que funcionam em qualquer tema */
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #1E293B !important; /* Azul Marinho quase preto */
    }

    /* Estilo dos campos de entrada (FORÇAR FUNDO CLARO E TEXTO ESCURO) */
    div[data-baseweb="input"], div[data-baseweb="number-input"], div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        border: 2px solid #3B82F6 !important;
        border-radius: 8px !important;
    }

    input {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* Estilo dos Cards (Borda forte para ver no escuro ou claro) */
    .med-card {
        background-color: #FFFFFF !important;
        border: 2px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-bottom: 10px !important;
        color: #000000 !important;
    }

    /* Botão Principal */
    div.stButton > button {
        background-color: #2563EB !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        height: 45px !important;
        width: 100% !important;
    }
    
    /* Sidebar Fixa */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #CBD5E1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.title("🏥 Menu")
    if "admin" not in st.session_state: st.session_state.admin = False
    
    if not st.session_state.admin:
        pw = st.text_input("Senha ADM", type="password")
        if pw == SENHA_ADM: 
            st.session_state.admin = True
            st.rerun()
    else:
        st.success("✅ Logado")
        if st.button("Sair"):
            st.session_state.admin = False
            st.rerun()
    
    menu = st.radio("Navegação", ["📊 Estoque", "🩺 Consultas", "💰 Financeiro", "➕ Cadastro", "🗑️ Remover"])

# --- 5. TELAS ---

if menu == "📊 Estoque":
    st.header("💊 Estoque de Remédios")
    df = api_get("remedios")
    if df.empty:
        st.info("Nada cadastrado.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            dias_passados = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_passados * r['dose_diaria'])))
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)
            
            # Alertas coloridos
            cor = "#EF4444" if dias_restantes < 7 else "#F59E0B" if dias_restantes < 15 else "#10B981"
            
            st.markdown(f"""
                <div class="med-card" style="border-left: 10px solid {cor} !important;">
                    <b style="font-size: 1.2em; color: black;">{r['nome'].upper()}</b><br>
                    <span style="color: #475569;">Estoque: {estoque_atual} un.</span><br>
                    <b style="color: {cor};">Acaba em: {data_fim.strftime('%d/%m/%Y')}</b>
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.admin:
                with st.expander(f"Repor {r['nome']}"):
                    n_q = st.number_input("Quantidade", 1, 500, 30, key=f"q_{r['id']}")
                    n_v = st.number_input("Preço R$", 0.0, 5000.0, float(r['preco']), key=f"v_{r['id']}")
                    if st.button("Confirmar Reposição", key=f"btn_{r['id']}"):
                        nova_qtd = estoque_atual + n_q
                        requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(nova_qtd), "data_inicio": str(hoje.date()), "preco": float(n_v)})
                        requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(n_v), "data_compra": str(hoje.date())})
                        enviar_telegram(f"✅ {r['nome']} reposto!")
                        st.success("Feito!"); time.sleep(1); st.rerun()

elif menu == "🗑️ Remover":
    st.header("🗑️ Excluir")
    if not st.session_state.admin: st.warning("Área Restrita.")
    else:
        tipo = st.selectbox("O que apagar?", ["Remédio", "Consulta", "Compra"])
        tab = {"Remédio":"remedios", "Consulta":"consultas", "Compra":"compras"}[tipo]
        df_d = api_get(tab)
        if not df_d.empty:
            col = 'nome' if tab == 'remedios' else 'medico' if tab == 'consultas' else 'nome_remedio'
            item = st.selectbox("Selecione:", df_d[col].tolist())
            id_i = df_d[df_d[col] == item]['id'].values[0]
            if st.button("❌ APAGAR"):
                requests.delete(f"{URL_SUPABASE}{tab}?id=eq.{id_i}", headers=HEADERS)
                enviar_telegram(f"🗑️ Removido: {item}")
                st.success("Excluído!"); time.sleep(1); st.rerun()

elif menu == "💰 Financeiro":
    st.header("💰 Resumo")
    df_r, df_c = api_get("compras"), api_get("consultas")
    t1 = df_r['valor'].sum() if not df_r.empty else 0
    t2 = df_c['valor'].sum() if not df_c.empty else 0
    st.subheader(f"Gasto Total: R$ {t1+t2:.2f}")
    if not df_r.empty: st.table(df_r[['data_compra', 'nome_remedio', 'valor']].head(10))

elif menu == "➕ Cadastro":
    if not st.session_state.admin: st.warning("Acesse como ADM.")
    else:
        c = st.selectbox("Tipo:", ["Remédio", "Consulta"])
        with st.form("cad"):
            if c == "Remédio":
                n, q, d, p = st.text_input("Nome"), st.number_input("Qtd", 1), st.number_input("Dose/dia", 1.0), st.number_input("Preço", 0.0)
            else:
                n, p = st.text_input("Médico"), st.number_input("Preço", 0.0)
            if st.form_submit_button("Salvar"):
                if c == "Remédio":
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                else:
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":n, "valor":float(p), "data_consulta":str(datetime.now().date())})
                st.success("Salvo!"); time.sleep(1); st.rerun()

elif menu == "🩺 Consultas":
    st.header("🩺 Histórico")
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            st.markdown(f'<div class="med-card"><b>{c["data_consulta"].strftime("%d/%m/%Y")}</b><br>Dr. {c["medico"]} - R$ {c["valor"]:.2f}</div>', unsafe_allow_html=True)
