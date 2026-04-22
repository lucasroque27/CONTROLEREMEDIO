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

# --- 3. DESIGN E CORES (MENU AZUL / LETRA BRANCA / CORPO BRANCO / LETRA PRETA) ---
st.set_page_config(page_title="Saúde Família", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA !important; }
    header[data-testid="stHeader"] { background-color: rgba(255, 255, 255, 0.9) !important; visibility: visible !important; }
    
    /* MENU LATERAL */
    [data-testid="stSidebar"] { background-color: #0A192F !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    
    /* CARDS DE REMÉDIO */
    .med-card {
        background-color: #FFFFFF !important;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        border: 2px solid #E2E8F0;
        border-left: 10px solid #3B82F6;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* TEXTO PRINCIPAL PRETO */
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label, .stMarkdown {
        color: #000000 !important;
        font-weight: 600;
    }
    
    div.stButton > button { width: 100%; border-radius: 8px; background-color: #3B82F6 !important; color: white !important; font-weight: bold; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. MENU LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🏥 Menu Saúde</h2>", unsafe_allow_html=True)
    st.markdown("---")
    if "admin" not in st.session_state: st.session_state.admin = False
    if not st.session_state.admin:
        pw = st.text_input("Senha ADM", type="password")
        if st.button("Liberar"):
            if pw == SENHA_ADM: st.session_state.admin = True; st.rerun()
            else: st.error("Senha Incorreta")
    else:
        st.success("Modo Edição Ativo")
        if st.button("Sair ADM"): st.session_state.admin = False; st.rerun()
    st.markdown("---")
    menu = st.radio("Ir para:", ["📊 Estoque", "🩺 Histórico", "💰 Financeiro", "➕ Cadastro", "🗑️ Remover"])

# --- 5. TELAS ---

if menu == "📊 Estoque":
    st.title("💊 Controle de Remédios")
    df = api_get("remedios")
    if df.empty:
        st.info("Nenhum remédio cadastrado.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            # CALCULO DE CONSUMO
            dias_passados = (hoje - r['data_inicio']).days
            consumo_ate_agora = dias_passados * r['dose_diaria']
            estoque_atual = max(0, int(r['qtd_total'] - consumo_ate_agora))
            
            # CALCULO DE QUANDO ACABA
            if r['dose_diaria'] > 0:
                dias_que_restam = int(estoque_atual / r['dose_diaria'])
                data_fim = hoje + timedelta(days=dias_que_restam)
            else:
                dias_que_restam = 0
                data_fim = hoje

            st.markdown(f"""
                <div class="med-card">
                    <span style="font-size: 1.3em; color: #000000 !important;"><b>{r['nome'].upper()}</b></span><br><br>
                    <span style="color: #000000 !important; font-size: 1.1em;">📦 Restam no estoque: <b>{estoque_atual} comprimidos</b></span><br>
                    <span style="color: #000000 !important;">📅 Vai acabar em: <b style="color: {'#CC0000' if dias_que_restam < 5 else '#000000'} !important;">{data_fim.strftime('%d/%m/%Y')}</b></span><br>
                    <span style="color: #000000 !important;">⏳ Duração: <b>{dias_que_restam} dias</b></span>
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.admin:
                with st.expander(f"➕ Adicionar mais {r['nome']}"):
                    nova_compra = st.number_input(f"Quantos comprimidos vieram na caixa nova?", min_value=1, value=30, key=f"in_{r['id']}")
                    if st.button("Confirmar Reposição", key=f"bt_{r['id']}"):
                        # Soma o que sobrou com o que comprou e reseta a data
                        nova_qtd_final = estoque_atual + nova_compra
                        api_patch("remedios", r['id'], {"qtd_total": int(nova_qtd_final), "data_inicio": str(hoje.date())})
                        api_post("compras", {"nome_remedio": r['nome'], "valor": float(r['preco']), "data_compra": str(hoje.date())})
                        st.success("Estoque atualizado!"); time.sleep(1); st.cache_data.clear(); st.rerun()

elif menu == "🩺 Histórico":
    st.title("🩺 Histórico de Consultas")
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            st.markdown(f"""
                <div class="med-card" style="border-left-color: #10B981;">
                    <span style="color: #000000 !important;">{c['data_consulta'].strftime('%d/%m/%Y')}</span><br>
                    <span style="font-size: 1.1em; color: #000000 !important;"><b>{c['medico']}</b></span><br>
                    <span style="color: #166534; font-weight: bold;">R$ {float(c.get('valor', 0)):.2f}</span>
                </div>
            """, unsafe_allow_html=True)

elif menu == "💰 Financeiro":
    st.title("💰 Gastos Totais")
    df_r = api_get("compras")
    df_c = api_get("consultas")
    t1, t2 = (df_r['valor'].sum() if not df_r.empty else 0), (df_c['valor'].sum() if not df_c.empty else 0)
    st.markdown(f"""
        <div class="med-card" style="text-align: center;">
            <h1 style="color: #000000 !important;">R$ {t1+t2:.2f}</h1>
            <p style="color: #000000 !important;">Remédios: R$ {t1:.2f} | Consultas: R$ {t2:.2f}</p>
        </div>
    """, unsafe_allow_html=True)
    if not df_r.empty:
        st.subheader("Histórico de Compras")
        st.write(df_r[['data_compra', 'nome_remedio', 'valor']])

elif menu == "➕ Cadastro":
    if not st.session_state.admin: st.warning("Acesse o modo ADM.")
    else:
        tipo = st.selectbox("O que cadastrar?", ["Remédio", "Consulta"])
        with st.form("c"):
            if tipo == "Remédio":
                n, q = st.text_input("Nome"), st.number_input("Qtd na Caixa", value=30)
                d, p = st.number_input("Doses por dia (ex: 4)", value=1.0), st.number_input("Preço", value=0.0)
                if st.form_submit_button("Salvar"):
                    api_post("remedios", {"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    api_post("compras", {"nome_remedio":n,"valor":float(p),"data_compra":str(datetime.now().date())})
                    st.success("Salvo!"); time.sleep(1); st.cache_data.clear(); st.rerun()
            else:
                m, v, dt = st.text_input("Médico"), st.number_input("Valor"), st.date_input("Data")
                if st.form_submit_button("Salvar"):
                    api_post("consultas", {"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    st.success("Salvo!"); time.sleep(1); st.cache_data.clear(); st.rerun()

elif menu == "🗑️ Remover":
    if not st.session_state.admin: st.warning("Acesse o modo ADM.")
    else:
        tab = st.selectbox("Tabela:", ["remedios", "consultas", "compras"])
        df_d = api_get(tab)
        if not df_d.empty:
            c = 'nome' if tab == 'remedios' else 'medico' if tab == 'consultas' else 'nome_remedio'
            item = st.selectbox("Item:", df_d[c].tolist())
            id_i = df_d[df_d[c] == item]['id'].values[0]
            if st.button("Remover"):
                api_delete(tab, id_i); st.success("Removido!"); time.sleep(1); st.cache_data.clear(); st.rerun()
