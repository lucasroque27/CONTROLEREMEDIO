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

# --- 2. FUNÇÕES ---
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

# --- 3. ESTILO CSS PROFISSIONAL ---
st.set_page_config(page_title="Saúde Pro", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    /* Estilo para os Cards de Remédios */
    .card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e1e4e8;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .card:hover {
        transform: translateY(-2px);
        border-color: #3b82f6;
    }
    .card-title {
        color: #1f2937;
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
    }
    .card-info {
        color: #4b5563;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    /* Estilização das métricas no topo */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #2563eb !important;
    }
    /* Deixar botões com cantos arredondados e cores sóbrias */
    div.stButton > button {
        border-radius: 8px !important;
        background-color: #2563eb !important;
        color: white !important;
        border: none !important;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #1d4ed8 !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063176.png", width=80)
    st.title("Saúde Família")
    
    if "admin" not in st.session_state: st.session_state.admin = False
    
    if not st.session_state.admin:
        with st.form("login_pro"):
            pw = st.text_input("Senha de Acesso", type="password")
            if st.form_submit_button("Entrar"):
                if pw == SENHA_ADM: 
                    st.session_state.admin = True
                    st.rerun()
                else: st.error("Incorreta")
    else:
        st.info("🔓 Modo Administrador")
        if st.button("Sair"):
            st.session_state.admin = False
            st.rerun()

    menu = st.radio("Navegação", ["📊 Dashboard", "🩺 Consultas", "💰 Financeiro", "➕ Gestão", "🗑️ Limpeza"])

# --- 5. LÓGICA DAS TELAS ---

if menu == "📊 Dashboard":
    st.title("📊 Controle de Medicamentos")
    df = api_get("remedios")
    
    if df.empty:
        st.info("Cadastre seu primeiro remédio na aba 'Gestão'.")
    else:
        # Métricas Rápidas
        col_m1, col_m2 = st.columns(2)
        hoje = datetime.now()
        remedios_baixos = 0
        
        # Loop para processar dados antes de exibir
        cards_html = ""
        for _, r in df.iterrows():
            dias_passados = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_passados * r['dose_diaria'])))
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)
            
            if dias_restantes < 7: 
                cor, label, remedios_baixos = "#ef4444", "Urgente", remedios_baixos + 1
            elif dias_restantes < 15: cor, label = "#f59e0b", "Atenção"
            else: cor, label = "#10b981", "Ok"

            st.markdown(f"""
                <div class="card">
                    <div class="card-title">
                        <span>{r['nome'].upper()}</span>
                        <span style="color: {cor}; font-size: 0.8rem;">● {label}</span>
                    </div>
                    <div class="card-info">
                        <b>Estoque Atual:</b> {estoque_atual} comprimidos/doses<br>
                        <b>Previsão de Término:</b> {data_fim.strftime('%d/%m/%Y')} ({dias_restantes} dias)
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if st.session_state.admin:
                with st.expander(f"⚙️ Ajustar {r['nome']}"):
                    n_q = st.number_input("Adicionar quantidade", 1, 500, 30, key=f"q_{r['id']}")
                    if st.button("Salvar Reposição", key=f"b_{r['id']}"):
                        nova_qtd = estoque_atual + n_q
                        requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(nova_qtd), "data_inicio": str(hoje.date())})
                        enviar_telegram(f"📦 Reposição: {r['nome']} (+{n_q} un.)")
                        st.success("Atualizado!"); time.sleep(1); st.rerun()

        col_m1.metric("Total de Itens", len(df))
        col_m2.metric("Críticos", remedios_baixos, delta_color="inverse")

elif menu == "➕ Gestão":
    st.title("➕ Gerenciar Dados")
    if not st.session_state.admin:
        st.warning("Apenas administradores podem cadastrar.")
    else:
        opcao = st.segmented_control("O que cadastrar?", ["Remédio", "Consulta"], default="Remédio")
        
        with st.container(border=True):
            if opcao == "Remédio":
                n = st.text_input("Nome Comercial")
                c1, c2 = st.columns(2)
                q = c1.number_input("Qtd total na caixa", 1)
                d = c2.number_input("Dose diária", 0.5, 10.0, 1.0)
                p = st.number_input("Valor pago (R$)", 0.0)
                if st.button("Finalizar Cadastro"):
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":n,"valor":float(p),"data_compra":str(datetime.now().date())})
                    st.success("Cadastrado!"); time.sleep(1); st.rerun()
            else:
                m = st.text_input("Médico / Especialidade")
                v = st.number_input("Valor da Consulta", 0.0)
                if st.button("Registrar Consulta"):
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":m, "valor":float(v), "data_consulta":str(datetime.now().date())})
                    st.success("Registrado!"); time.sleep(1); st.rerun()

elif menu == "🗑️ Limpeza":
    st.title("🗑️ Remover Registros")
    if not st.session_state.admin: st.error("Acesso negado.")
    else:
        t_del = st.selectbox("Escolha a categoria", ["remedios", "consultas", "compras"])
        df_del = api_get(t_del)
        if not df_del.empty:
            col_ref = 'nome' if t_del == 'remedios' else 'medico' if t_del == 'consultas' else 'nome_remedio'
            item_del = st.selectbox("Selecione o item para remover", df_del[col_ref].tolist())
            id_del = df_del[df_del[col_ref] == item_del]['id'].values[0]
            
            if st.button("Excluir Permanentemente"):
                requests.delete(f"{URL_SUPABASE}{t_del}?id=eq.{id_del}", headers=HEADERS)
                st.toast(f"✅ {item_del} removido com sucesso!")
                time.sleep(1); st.rerun()

elif menu == "💰 Financeiro":
    st.title("💰 Controle de Gastos")
    df_r, df_c = api_get("compras"), api_get("consultas")
    total = (df_r['valor'].sum() if not df_r.empty else 0) + (df_c['valor'].sum() if not df_c.empty else 0)
    
    st.metric("Investimento Total em Saúde", f"R$ {total:.2f}")
    
    tab1, tab2 = st.tabs(["Histórico de Compras", "Histórico de Consultas"])
    with tab1: st.dataframe(df_r, use_container_width=True)
    with tab2: st.dataframe(df_c, use_container_width=True)

elif menu == "🩺 Consultas":
    st.title("🩺 Próximas & Passadas")
    df_c = api_get("consultas")
    if df_c.empty: st.info("Nenhuma consulta registrada.")
    else:
        for _, c in df_c.iterrows():
            st.markdown(f"""
                <div class="card" style="border-left: 5px solid #2563eb;">
                    <div class="card-title">{c['medico']}</div>
                    <div class="card-info">
                        📅 Data: {c['data_consulta'].strftime('%d/%m/%Y')}<br>
                        💸 Valor: R$ {c['valor']:.2f}
                    </div>
                </div>
            """, unsafe_allow_html=True)
