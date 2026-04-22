import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import time

# --- 1. CONFIGURAÇÕES SUPABASE ---
URL_SUPABASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"

HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

SENHA_ADM = "1234"
TELEGRAM_TOKEN = "8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM"
LISTA_IDS = ["5256921022"]

# --- 2. FUNÇÕES DE COMUNICAÇÃO ---
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

def api_post(tabela, dados):
    res = requests.post(URL_SUPABASE + tabela, headers=HEADERS, json=dados)
    return res.status_code

def api_patch(tabela, id_item, dados):
    res = requests.patch(f"{URL_SUPABASE}{tabela}?id=eq.{id_item}", headers=HEADERS, json=dados)
    return res.status_code

def api_delete(tabela, id_item):
    requests.delete(f"{URL_SUPABASE}{tabela}?id=eq.{id_item}", headers=HEADERS)

def enviar_telegram(msg):
    for cid in LISTA_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try: requests.post(url, json={"chat_id": cid, "text": msg, "parse_mode": "Markdown"})
        except: pass

# --- 3. INTERFACE ---
st.set_page_config(page_title="Saúde Família", page_icon="💊", layout="centered")

# CSS para evitar que o layout quebre
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .card { background: white; padding: 15px; border-radius: 12px; border-left: 5px solid #1A237E; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .metric-card { background: #E8F5E9; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #A5D6A7; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

if "admin" not in st.session_state: st.session_state.admin = False
with st.sidebar:
    st.title("🔐 Acesso")
    if not st.session_state.admin:
        pw = st.text_input("Senha", type="password")
        if st.button("Liberar"):
            if pw == SENHA_ADM: st.session_state.admin = True; st.rerun()
            else: st.error("Senha Incorreta")
    else:
        st.success("Modo Edição Ativo")
        if st.button("Sair"): st.session_state.admin = False; st.rerun()

menu = st.sidebar.radio("Navegação", ["📊 Estoque", "🩺 Consultas", "💰 Financeiro", "➕ Cadastro", "🗑️ Remover"])

# --- 5. TELAS ---

if menu == "📊 Estoque":
    st.header("💊 Estoque de Medicamentos")
    df = api_get("remedios")
    if df.empty: st.info("Nenhum remédio cadastrado.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            dias_p = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_p * r['dose_diaria'])))
            dias_r = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            
            with st.expander(f"💊 {r['nome'].upper()} - {estoque_atual} un."):
                st.write(f"Previsão: {(hoje + timedelta(days=dias_r)).strftime('%d/%m/%Y')}")
                if st.session_state.admin:
                    adicao = st.number_input("Somar quantidade", min_value=1, value=30, key=f"add_{r['id']}")
                    if st.button("Confirmar Soma", key=f"btn_{r['id']}"):
                        nova_qtd = estoque_atual + adicao
                        api_patch("remedios", r['id'], {"qtd_total": int(nova_qtd), "data_inicio": str(hoje.date())})
                        api_post("compras", {"nome_remedio": r['nome'], "valor": float(r['preco']), "data_compra": str(hoje.date())})
                        st.success("Estoque atualizado!")
                        time.sleep(1)
                        st.cache_data.clear()
                        st.rerun()

elif menu == "🩺 Consultas":
    st.header("🩺 Consultas")
    df_cons = api_get("consultas")
    if not df_cons.empty:
        df_v = df_cons.copy()
        df_v['data_consulta'] = df_v['data_consulta'].dt.strftime('%d/%m/%Y')
        for _, c in df_v.iterrows():
            st.markdown(f"""<div class="card"><b>{c['data_consulta']} - {c['medico']}</b><br>Valor: R$ {float(c.get('valor', 0)):.2f}</div>""", unsafe_allow_html=True)

elif menu == "💰 Financeiro":
    st.header("💰 Controle Financeiro")
    df_compras = api_get("compras")
    df_consultas = api_get("consultas")
    tr = df_compras['valor'].sum() if not df_compras.empty else 0
    tc = df_consultas['valor'].sum() if not df_consultas.empty else 0
    st.metric("Total Investido", f"R$ {tr + tc:.2f}")

elif menu == "➕ Cadastro":
    if not st.session_state.admin: st.warning("Acesse com a senha.")
    else:
        tipo = st.selectbox("Registrar:", ["Medicamento", "Consulta"])
        with st.form("cadastro"):
            if tipo == "Medicamento":
                n, q = st.text_input("Nome"), st.number_input("Qtd", value=30)
                d, p = st.number_input("Dose/Dia", value=1.0), st.number_input("Preço", value=0.0)
                if st.form_submit_button("Salvar"):
                    api_post("remedios", {"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    api_post("compras", {"nome_remedio":n,"valor":float(p),"data_compra":str(datetime.now().date())})
                    st.success("Salvo!")
                    time.sleep(1)
                    st.cache_data.clear()
                    st.rerun()
            else:
                m, v = st.text_input("Médico"), st.number_input("Valor", value=0.0)
                dt = st.date_input("Data")
                if st.form_submit_button("Salvar"):
                    api_post("consultas", {"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    st.success("Consulta registrada!")
                    time.sleep(1)
                    st.cache_data.clear()
                    st.rerun()

elif menu == "🗑️ Remover":
    if not st.session_state.admin: st.warning("Acesso restrito.")
    else:
        tabela = st.selectbox("Categoria:", ["remedios", "consultas", "compras"])
        df_del = api_get(tabela)
        if not df_del.empty:
            col = 'nome' if tabela == 'remedios' else 'medico' if tabela == 'consultas' else 'nome_remedio'
            item = st.selectbox("Item:", df_del[col].tolist())
            id_it = df_del[df_del[col] == item]['id'].values[0]
            if st.button("EXCLUIR"):
                api_delete(tabela, id_it)
                st.success("Excluído!")
                time.sleep(1)
                st.cache_data.clear()
                st.rerun()
