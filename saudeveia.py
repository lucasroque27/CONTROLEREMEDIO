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

# --- 3. CONFIGURAÇÃO VISUAL (DESIGN DE APP - ALTO CONTRASTE) ---
st.set_page_config(page_title="Saúde Família", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    /* 1. Força Fundo Branco em Tudo */
    .stApp, [data-testid="stVerticalBlock"], [data-testid="stExpander"], .st-emotion-cache-1kyx60n {
        background-color: #FFFFFF !important;
    }
    
    /* 2. FORÇA LETRA PRETA ABSOLUTA EM TUDO (*) */
    * {
        color: #000000 !important;
    }

    /* 3. Ajuste para Títulos e Textos Principais */
    h1, h2, h3, b, strong, p, span, label, .stMarkdown {
        color: #000000 !important;
        font-weight: 700 !important;
    }

    /* 4. Cards Modernos com Borda Escura para não "sumir" */
    .med-card {
        background-color: #F8F9FA !important;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 15px;
        border: 2px solid #1E3A8A !important; /* Borda azul marinho forte */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* 5. Cores de Status (Mais fortes para leitura fácil) */
    .status-critico { color: #CC0000 !important; font-weight: 900 !important; font-size: 1.2em; }
    .status-ok { color: #006600 !important; font-weight: 900 !important; font-size: 1.2em; }

    /* 6. Botões Grandes e Escuros */
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        background-color: #001A3D !important;
        color: #FFFFFF !important; /* Letra branca no botão escuro */
        font-weight: bold;
        border: none;
    }

    /* Esconder o menu padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. CONTROLE DE ACESSO ---
if "admin" not in st.session_state: st.session_state.admin = False
with st.sidebar:
    st.title("Menu")
    if not st.session_state.admin:
        pw = st.text_input("🔑 Senha ADM", type="password")
        if st.button("Liberar Edição"):
            if pw == SENHA_ADM: 
                st.session_state.admin = True
                st.cache_data.clear()
                st.rerun()
            else: st.error("Senha Incorreta")
    else:
        st.success("✨ Administrador Ativo")
        if st.button("🔒 Sair"): 
            st.session_state.admin = False
            st.cache_data.clear()
            st.rerun()

menu = st.sidebar.radio("Navegação:", ["📊 Estoque", "🩺 Consultas", "💰 Gastos", "➕ Cadastrar", "🗑️ Remover"])

# --- 5. TELAS ---

if menu == "📊 Estoque":
    st.header("💊 Estoque de Medicamentos")
    df = api_get("remedios")
    if df.empty:
        st.info("Nada cadastrado ainda.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            dias_pados = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_pados * r['dose_diaria'])))
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            
            # Título em Preto Forte
            with st.expander(f"📦 {r['nome'].upper()} - Restam {estoque_atual}"):
                st.markdown(f"""
                    <div class="med-card">
                        <b style="font-size: 1.2em;">{r['nome'].upper()}</b><br><br>
                        <span class="{'status-critico' if dias_restantes <= 7 else 'status-ok'}">
                            ESTOQUE: {estoque_atual} unidades
                        </span><br>
                        <span>Duração: Aprox. <b>{dias_restantes} dias</b></span><br>
                        <span>Acaba em: <b>{(hoje + timedelta(days=dias_restantes)).strftime('%d/%m/%Y')}</b></span>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.session_state.admin:
                    st.write("---")
                    adicao = st.number_input(f"Somar ao {r['nome']}", min_value=1, value=30, key=f"add_{r['id']}")
                    if st.button("Confirmar Soma", key=f"btn_{r['id']}"):
                        nova_qtd = estoque_atual + adicao
                        api_patch("remedios", r['id'], {"qtd_total": int(nova_qtd), "data_inicio": str(hoje.date())})
                        api_post("compras", {"nome_remedio": r['nome'], "valor": float(r['preco']), "data_compra": str(hoje.date())})
                        st.success("Atualizado!"); time.sleep(1); st.cache_data.clear(); st.rerun()

elif menu == "🩺 Consultas":
    st.header("🩺 Histórico Médico")
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            st.markdown(f"""
                <div class="med-card">
                    <b>Data: {c['data_consulta'].strftime('%d/%m/%Y')}</b><br>
                    <span style="font-size: 1.1em;">Médico: <b>{c['medico']}</b></span><br>
                    <span>Valor: R$ {float(c.get('valor', 0)):.2f}</span>
                </div>
            """, unsafe_allow_html=True)

elif menu == "💰 Gastos":
    st.header("💰 Financeiro")
    df_compras = api_get("compras")
    df_consultas = api_get("consultas")
    t1 = df_compras['valor'].sum() if not df_compras.empty else 0
    t2 = df_consultas['valor'].sum() if not df_consultas.empty else 0
    
    st.markdown(f"""
        <div class="med-card" style="text-align: center; border-left: 10px solid #006600 !important;">
            <h2 style="margin:0;">Total: R$ {t1+t2:.2f}</h2>
            <p>Remédios: R$ {t1:.2f} | Consultas: R$ {t2:.2f}</p>
        </div>
    """, unsafe_allow_html=True)

elif menu == "➕ Cadastrar":
    if not st.session_state.admin: 
        st.warning("⚠️ Use a senha para cadastrar.")
    else:
        opcao = st.selectbox("Tipo:", ["Remédio", "Consulta"])
        with st.form("f_cad"):
            if opcao == "Remédio":
                n = st.text_input("Nome")
                q = st.number_input("Qtd total", value=30)
                d = st.number_input("Dose/dia", value=1.0)
                p = st.number_input("Preço", value=0.0)
                if st.form_submit_button("Salvar"):
                    api_post("remedios", {"nome":n, "qtd_total":int(q), "dose_diaria":float(d), "preco":float(p), "data_inicio":str(datetime.now().date())})
                    api_post("compras", {"nome_remedio":n, "valor":float(p), "data_compra":str(datetime.now().date())})
                    st.success("Salvo!"); time.sleep(1); st.cache_data.clear(); st.rerun()
            else:
                m = st.text_input("Médico")
                v = st.number_input("Valor", value=0.0)
                dt = st.date_input("Data")
                if st.form_submit_button("Salvar"):
                    api_post("consultas", {"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    st.success("Salvo!"); time.sleep(1); st.cache_data.clear(); st.rerun()

elif menu == "🗑️ Remover":
    if not st.session_state.admin:
        st.warning("⚠️ Acesso restrito.")
    else:
        tab = st.selectbox("Local:", ["remedios", "consultas", "compras"])
        df_d = api_get(tab)
        if not df_d.empty:
            col_nome = 'nome' if tab == 'remedios' else 'medico' if tab == 'consultas' else 'nome_remedio'
            escolha = st.selectbox("Item:", df_d[col_nome].tolist())
            id_item = df_d[df_d[col_nome] == escolha]['id'].values[0]
            if st.button("🔴 EXCLUIR"):
                api_delete(tab, id_item)
                st.success("Removido!"); time.sleep(1); st.cache_data.clear(); st.rerun()
