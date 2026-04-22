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

# --- 3. DESIGN DO APLICATIVO (UI/UX) ---
st.set_page_config(page_title="Saúde Família", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    /* FUNDO GERAL */
    .stApp { background-color: #F8F9FA !important; }

    /* ESTILIZAÇÃO DA BARRA LATERAL (SIDEBAR) */
    [data-testid="stSidebar"] {
        background-color: #0A192F !important; /* Azul Marinho Profundo */
        border-right: 1px solid #1E293B;
    }
    
    /* Texto da Sidebar */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }

    /* Estilo dos Rádios (Navegação) na Sidebar */
    [data-testid="stSidebar"] .st-emotion-cache-17l6f7z, [data-testid="stSidebar"] .st-emotion-cache-6q9sum {
        background-color: transparent !important;
        color: white !important;
    }

    /* CARDS DE CONTEÚDO (ESTOQUE/CONSULTAS) */
    .med-card {
        background-color: #FFFFFF !important;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #E2E8F0;
        border-left: 8px solid #3B82F6; /* Borda lateral azul */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* TEXTOS NO CORPO DO APP (SEMPRE PRETO) */
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label {
        color: #1E293B !important;
        font-weight: 600;
    }

    /* BOTÕES */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        background-color: #3B82F6 !important;
        color: white !important;
        border: none;
        padding: 10px;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #2563EB !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }

    /* ESCONDER ELEMENTOS DESNECESSÁRIOS */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. BARRA LATERAL (MENU) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🏥 Painel Saúde</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    if "admin" not in st.session_state: st.session_state.admin = False
    
    if not st.session_state.admin:
        st.markdown("🔒 **Área Restrita**")
        pw = st.text_input("Senha ADM", type="password", help="Insira a senha para habilitar edições")
        if st.button("Liberar Acesso"):
            if pw == SENHA_ADM:
                st.session_state.admin = True
                st.rerun()
            else: st.error("Senha incorreta")
    else:
        st.success("🔓 Modo Edição Ativo")
        if st.button("Sair do Modo ADM"):
            st.session_state.admin = False
            st.rerun()
    
    st.markdown("---")
    menu = st.radio("Navegação", ["📊 Estoque", "🩺 Consultas", "💰 Gastos", "➕ Cadastro", "🗑️ Remover"])

# --- 5. LÓGICA DAS TELAS ---

if menu == "📊 Estoque":
    st.title("💊 Controle de Medicamentos")
    df = api_get("remedios")
    if df.empty:
        st.info("Nenhum remédio no sistema.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            dias_pados = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_pados * r['dose_diaria'])))
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            
            st.markdown(f"""
                <div class="med-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.2em; color: #1E293B;"><b>{r['nome'].upper()}</b></span>
                        <span style="background: {'#FEE2E2' if dias_restantes <= 7 else '#DCFCE7'}; 
                                     color: {'#991B1B' if dias_restantes <= 7 else '#166534'}; 
                                     padding: 4px 12px; border-radius: 20px; font-size: 0.9em; font-weight: bold;">
                            {estoque_atual} un.
                        </span>
                    </div>
                    <p style="margin-top: 10px; color: #64748B; font-size: 0.95em;">
                        ⏳ Dura aprox. <b>{dias_restantes} dias</b><br>
                        📅 Término previsto: <b>{(hoje + timedelta(days=dias_restantes)).strftime('%d/%m/%Y')}</b>
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.admin:
                with st.expander(f"⚙️ Gerenciar {r['nome']}"):
                    adicao = st.number_input(f"Somar unidades", min_value=1, value=30, key=f"add_{r['id']}")
                    if st.button("Salvar Reabastecimento", key=f"btn_{r['id']}"):
                        nova_qtd = estoque_atual + adicao
                        api_patch("remedios", r['id'], {"qtd_total": int(nova_qtd), "data_inicio": str(hoje.date())})
                        api_post("compras", {"nome_remedio": r['nome'], "valor": float(r['preco']), "data_compra": str(hoje.date())})
                        st.success("Estoque Atualizado!")
                        time.sleep(0.5); st.cache_data.clear(); st.rerun()

elif menu == "🩺 Consultas":
    st.title("🩺 Histórico Médico")
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            st.markdown(f"""
                <div class="med-card" style="border-left-color: #10B981;">
                    <span style="color: #64748B; font-size: 0.85em;">{c['data_consulta'].strftime('%d/%m/%Y')}</span><br>
                    <span style="font-size: 1.1em; color: #1E293B;"><b>{c['medico']}</b></span><br>
                    <span style="color: #059669; font-weight: bold;">R$ {float(c.get('valor', 0)):.2f}</span>
                </div>
            """, unsafe_allow_html=True)
    else: st.info("Sem consultas registradas.")

elif menu == "💰 Gastos":
    st.title("💰 Financeiro")
    df_rem = api_get("compras")
    df_con = api_get("consultas")
    t1 = df_rem['valor'].sum() if not df_rem.empty else 0
    t2 = df_con['valor'].sum() if not df_con.empty else 0
    
    st.markdown(f"""
        <div class="med-card" style="text-align: center; border-left: none; border-top: 5px solid #3B82F6;">
            <p style="color: #64748B; margin-bottom: 5px;">Investimento Total</p>
            <h1 style="color: #1E293B; margin: 0;">R$ {t1+t2:.2f}</h1>
            <div style="display: flex; justify-content: space-around; margin-top: 20px;">
                <div><small>Remédios</small><br><b style="color: #3B82F6;">R$ {t1:.2f}</b></div>
                <div><small>Consultas</small><br><b style="color: #10B981;">R$ {t2:.2f}</b></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

elif menu == "➕ Cadastro":
    if not st.session_state.admin:
        st.warning("Acesse o modo administrador na barra lateral para cadastrar.")
    else:
        st.title("➕ Novo Cadastro")
        tipo = st.selectbox("O que deseja registrar?", ["Medicamento", "Consulta"])
        with st.form("cad_form"):
            if tipo == "Medicamento":
                n = st.text_input("Nome do Remédio")
                q = st.number_input("Qtd na Caixa", value=30)
                d = st.number_input("Dose Diária", value=1.0)
                p = st.number_input("Preço da Caixa", value=0.0)
                if st.form_submit_button("Finalizar Cadastro"):
                    api_post("remedios", {"nome":n, "qtd_total":int(q), "dose_diaria":float(d), "preco":float(p), "data_inicio":str(datetime.now().date())})
                    api_post("compras", {"nome_remedio":n, "valor":float(p), "data_compra":str(datetime.now().date())})
                    st.success("Cadastrado!"); time.sleep(0.5); st.cache_data.clear(); st.rerun()
            else:
                m = st.text_input("Médico / Especialidade")
                v = st.number_input("Valor pago", value=0.0)
                dt = st.date_input("Data")
                if st.form_submit_button("Registrar Consulta"):
                    api_post("consultas", {"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    st.success("Registrado!"); time.sleep(0.5); st.cache_data.clear(); st.rerun()

elif menu == "🗑️ Remover":
    if not st.session_state.admin:
        st.warning("Acesso restrito.")
    else:
        st.title("🗑️ Remover Registro")
        tabela = st.selectbox("Categoria:", ["remedios", "consultas", "compras"])
        df_del = api_get(tabela)
        if not df_del.empty:
            col = 'nome' if tabela == 'remedios' else 'medico' if tabela == 'consultas' else 'nome_remedio'
            item = st.selectbox("Escolha o item:", df_del[col].tolist())
            id_it = df_del[df_del[col] == item]['id'].values[0]
            if st.button("Confirmar Exclusão"):
                api_delete(tabela, id_it)
                st.success("Excluído!"); time.sleep(0.5); st.cache_data.clear(); st.rerun()
