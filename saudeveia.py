import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import time

# --- 1. CONFIGURAÇÕES (SUPABASE E TELEGRAM RECUPERADOS) ---
URL_SUPABASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"

# Credenciais recuperadas do seu histórico
TOKEN_TELEGRAM = "8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM"import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import time

# --- 1. CONFIGURAÇÕES ---
URL_SUPABASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"

# Credenciais recuperadas
TOKEN_TELEGRAM = "8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM"
CHAT_ID = "5256921022"

HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. FUNÇÃO DE ENVIO (COM LOG DE ERRO) ---
def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem})
        return res.status_code == 200
    except Exception as e:
        st.error(f"Erro ao conectar com Telegram: {e}")
        return False

# --- 3. ESTILO CSS ---
st.set_page_config(page_title="Saúde Família", page_icon="💊", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    [data-testid="stSidebar"] { background-color: #0A192F !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    .med-card {
        background-color: #F8F9FA !important;
        border-radius: 15px; padding: 20px; margin-bottom: 20px;
        border-left: 12px solid #3B82F6;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label, .stMarkdown {
        color: #000000 !important; font-weight: 600;
    }
    div.stButton > button { width: 100%; border-radius: 10px; background-color: #3B82F6 !important; color: white !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🏥 Painel de Controle</h2>", unsafe_allow_html=True)
    
    # BOTÃO DE TESTE DIRETO
    st.markdown("---")
    st.markdown("⚡ **Teste de Conexão**")
    if st.button("Enviar Mensagem de Teste"):
        if enviar_telegram("🚀 Teste de conexão: O bot está ativo!"):
            st.success("Mensagem enviada! Verifique seu Telegram.")
        else:
            st.error("Falha no envio. Verifique o Token/ID.")
    st.markdown("---")
    
    if "admin" not in st.session_state: st.session_state.admin = False
    if not st.session_state.admin:
        pw = st.text_input("Senha ADM", type="password")
        if st.button("Liberar"):
            if pw == "1234": st.session_state.admin = True; st.rerun()
    else:
        st.success("Modo Edição Ativo")
        if st.button("Sair ADM"): st.session_state.admin = False; st.rerun()

    menu = st.radio("Menu", ["📊 Estoque", "🩺 Histórico", "💰 Financeiro", "➕ Cadastro", "🗑️ Remover"])

# --- 5. LÓGICA PRINCIPAL (ESTOQUE) ---
if menu == "📊 Estoque":
    st.title("💊 Controle de Remédios")
    df = requests.get(f"{URL_SUPABASE}remedios?select=*&order=id.desc", headers=HEADERS).json()
    if not df:
        st.info("Sem dados.")
    else:
        hoje = datetime.now()
        for r in df:
            data_ini = pd.to_datetime(r['data_inicio'])
            dias_passados = (hoje - data_ini).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_passados * r['dose_diaria'])))
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)

            st.markdown(f"""
                <div class="med-card">
                    <span style="font-size: 1.4em;"><b>{r['nome'].upper()}</b></span><br>
                    <p>📦 Estoque: <b>{estoque_atual} un.</b> | 🕒 Dose: <b>{r['dose_diaria']} p/ dia</b></p>
                    <p style="color: {'#CC0000' if dias_restantes < 5 else '#006600'} !important;">
                        📅 Acaba em: <b>{data_fim.strftime('%d/%m/%Y')}</b> ({dias_restantes} dias)
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.admin:
                with st.expander(f"Repor {r['nome']}"):
                    with st.form(f"f_{r['id']}"):
                        n_qtd = st.number_input("Qtd nova", value=30)
                        n_val = st.number_input("Preço", value=float(r['preco']))
                        if st.form_submit_button("Repor"):
                            novo_total = estoque_atual + n_qtd
                            requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(novo_total), "data_inicio": str(hoje.date()), "preco": float(n_val)})
                            requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(n_val), "data_compra": str(hoje.date())})
                            enviar_telegram(f"✅ REPOSIÇÃO: {r['nome']}\n📦 Total: {novo_total} un.\n📅 Dura até: {(hoje + timedelta(days=int(novo_total/r['dose_diaria']))).strftime('%d/%m/%Y')}")
                            st.rerun()

# --- DEMAIS TELAS (RESUMIDAS PARA ECONOMIA) ---
elif menu == "💰 Financeiro":
    st.title("💰 Gastos")
    compras = requests.get(f"{URL_SUPABASE}compras?select=*", headers=HEADERS).json()
    if compras: st.dataframe(pd.DataFrame(compras)[['data_compra', 'nome_remedio', 'valor']])

elif menu == "➕ Cadastro":
    if st.session_state.admin:
        with st.form("novo"):
            n = st.text_input("Nome")
            q = st.number_input("Qtd", value=30)
            d = st.number_input("Dose/dia", value=1.0)
            p = st.number_input("Preço", value=0.0)
            if st.form_submit_button("Salvar"):
                requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                enviar_telegram(f"🆕 CADASTRO: {n}\n📦 {q} un.")
                st.rerun()
CHAT_ID = "5256921022"

HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

SENHA_ADM = "1234"

# --- 2. FUNÇÕES DE COMUNICAÇÃO ---
def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem})
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

def api_post(tabela, dados):
    return requests.post(URL_SUPABASE + tabela, headers=HEADERS, json=dados).status_code

def api_patch(tabela, id_item, dados):
    return requests.patch(f"{URL_SUPABASE}{tabela}?id=eq.{id_item}", headers=HEADERS, json=dados).status_code

def api_delete(tabela, id_item):
    requests.delete(f"{URL_SUPABASE}{tabela}?id=eq.{id_item}", headers=HEADERS)

# --- 3. ESTILO CSS (ALTO CONTRASTE) ---
st.set_page_config(page_title="Saúde Família", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    
    /* SIDEBAR AZUL COM LETRA BRANCA */
    [data-testid="stSidebar"] { 
        background-color: #0A192F !important; 
    }
    [data-testid="stSidebar"] * { 
        color: #FFFFFF !important; 
    }
    
    /* CABEÇALHO */
    header[data-testid="stHeader"] { background-color: white !important; visibility: visible !important; }
    
    /* CARDS DA TELA PRINCIPAL */
    .med-card {
        background-color: #F8F9FA !important;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 12px solid #3B82F6;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    /* TEXTO PRETO NO CORPO */
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label, .stMarkdown {
        color: #000000 !important; font-weight: 600;
    }
    
    div.stButton > button { 
        width: 100%; border-radius: 10px; background-color: #3B82F6 !important; color: white !important; font-weight: bold; 
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🏥 Gestão Saúde</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    if "admin" not in st.session_state: st.session_state.admin = False
    
    if not st.session_state.admin:
        pw = st.text_input("Acesso ADM (Senha)", type="password")
        if st.button("Liberar"):
            if pw == SENHA_ADM: 
                st.session_state.admin = True
                st.rerun()
            else: st.error("Senha Incorreta")
    else:
        st.success("✨ Modo Edição Ativo")
        if st.button("Sair do Modo ADM"):
            st.session_state.admin = False
            st.rerun()
            
    st.markdown("---")
    menu = st.radio("Navegação", ["📊 Estoque", "🩺 Histórico Médico", "💰 Financeiro", "➕ Cadastro", "🗑️ Remover"])

# --- 5. LÓGICA DAS TELAS ---

if menu == "📊 Estoque":
    st.title("💊 Controle de Remédios")
    df = api_get("remedios")
    if df.empty:
        st.info("Nenhum remédio cadastrado.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            # Cálculo de consumo
            dias_passados = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_passados * r['dose_diaria'])))
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)

            st.markdown(f"""
                <div class="med-card">
                    <span style="font-size: 1.4em;"><b>{r['nome'].upper()}</b></span><br>
                    <p style="margin:8px 0;">📦 Estoque: <b>{estoque_atual} un.</b> | 🕒 Dose: <b>{r['dose_diaria']} un./dia</b></p>
                    <p style="font-size: 1.2em; color: {'#CC0000' if dias_restantes < 5 else '#006600'} !important;">
                        📅 Acaba em: <b>{data_fim.strftime('%d/%m/%Y')}</b><br>
                        ⏳ Restam: <b>{dias_restantes} dias</b>
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.admin:
                with st.expander(f"🔄 Repor {r['nome']}"):
                    with st.form(f"f_{r['id']}"):
                        n_qtd = st.number_input("Qtd comprada agora", min_value=1, value=30)
                        n_val = st.number_input("Preço da caixa (R$)", min_value=0.0, value=float(r['preco']))
                        if st.form_submit_button("Confirmar Reposição"):
                            total_novo = estoque_atual + n_qtd
                            api_patch("remedios", r['id'], {"qtd_total": int(total_novo), "data_inicio": str(hoje.date()), "preco": float(n_val)})
                            api_post("compras", {"nome_remedio": r['nome'], "valor": float(n_val), "data_compra": str(hoje.date())})
                            
                            enviar_telegram(f"✅ ESTOQUE ATUALIZADO: {r['nome']}\n📦 Agora tem: {total_novo} un.\n💰 Gasto: R$ {n_val:.2f}\n📅 Dura até: {(hoje + timedelta(days=int(total_novo/r['dose_diaria']))).strftime('%d/%m/%Y')}")
                            st.success("Atualizado!"); time.sleep(1); st.cache_data.clear(); st.rerun()

elif menu == "🩺 Histórico Médico":
    st.title("🩺 Consultas Realizadas")
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            st.markdown(f"""
                <div class="med-card" style="border-left-color: #10B981;">
                    <b>{c['data_consulta'].strftime('%d/%m/%Y')}</b><br>
                    <span style="font-size:1.1em;">Dr(a). {c['medico']}</span><br>
                    <span style="color: #166534;">Valor: R$ {float(c.get('valor', 0)):.2f}</span>
                </div>
            """, unsafe_allow_html=True)

elif menu == "💰 Financeiro":
    st.title("💰 Resumo de Gastos")
    df_r, df_c = api_get("compras"), api_get("consultas")
    t1 = df_r['valor'].sum() if not df_r.empty else 0
    t2 = df_c['valor'].sum() if not df_c.empty else 0
    
    st.metric("Gasto Total", f"R$ {t1+t2:.2f}")
    
    if not df_r.empty:
        st.subheader("🛒 Histórico de Compras de Remédios")
        st.dataframe(df_r[['data_compra', 'nome_remedio', 'valor']], use_container_width=True)

elif menu == "➕ Cadastro":
    if not st.session_state.admin:
        st.warning("🔒 Acesse o Modo ADM para cadastrar.")
    else:
        tipo = st.selectbox("O que deseja cadastrar?", ["Remédio", "Consulta"])
        with st.form("cad_novo"):
            if tipo == "Remédio":
                n = st.text_input("Nome do Remédio")
                q = st.number_input("Quantidade na Caixa", value=30)
                d = st.number_input("Dose diária (Ex: 4)", value=1.0)
                p = st.number_input("Preço da Caixa", value=0.0)
                if st.form_submit_button("Salvar Medicamento"):
                    api_post("remedios", {"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    api_post("compras", {"nome_remedio":n,"valor":float(p),"data_compra":str(datetime.now().date())})
                    enviar_telegram(f"🆕 NOVO CADASTRO: {n}\n📦 Caixa com: {q}\n🕒 Dose: {d}/dia\n💰 Valor: R$ {p}")
                    st.success("Salvo!"); time.sleep(1); st.cache_data.clear(); st.rerun()
            else:
                m = st.text_input("Médico / Especialidade")
                v = st.number_input("Valor", value=0.0)
                dt = st.date_input("Data")
                if st.form_submit_button("Salvar Consulta"):
                    api_post("consultas", {"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    enviar_telegram(f"🩺 NOVA CONSULTA: {m}\n📅 Data: {dt}\n💰 Valor: R$ {v}")
                    st.success("Registrado!"); time.sleep(1); st.cache_data.clear(); st.rerun()

elif menu == "🗑️ Remover":
    if not st.session_state.admin:
        st.warning("🔒 Acesso restrito ao ADM.")
    else:
        tabela = st.selectbox("Escolha onde apagar:", ["remedios", "consultas", "compras"])
        df_d = api_get(tabela)
        if not df_d.empty:
            col = 'nome' if tabela == 'remedios' else 'medico' if tabela == 'consultas' else 'nome_remedio'
            it = st.selectbox("Item para remover:", df_d[col].tolist())
            if st.button("❌ EXCLUIR DEFINITIVAMENTE"):
                api_delete(tabela, df_d[df_d[col] == it]['id'].values[0])
                st.success("Removido!"); time.sleep(1); st.cache_data.clear(); st.rerun()
