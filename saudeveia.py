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

# --- 3. ESTILO CSS: BLOQUEIO TOTAL DE MODO ESCURO ---
st.set_page_config(page_title="Saúde Família", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    /* 1. Forçar Fundo Claro na Estrutura Principal */
    [data-testid="stAppViewContainer"], .stApp, [data-testid="stHeader"] {
        background-color: #F4F6F9 !important;
    }
    
    /* 2. Forçar Fundo Branco na Barra Lateral */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 2px solid #E0E0E0 !important;
    }

    /* 3. Forçar TODO O TEXTO para PRETO */
    p, span, h1, h2, h3, h4, h5, h6, label, div[data-testid="stMarkdownContainer"] * {
        color: #000000 !important;
    }

    /* 4. Caixas de Texto / Inputs (Fundo branco, borda cinza, letra preta) */
    div[data-baseweb="input"], div[data-baseweb="number-input"], div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        border: 2px solid #A0A0A0 !important;
        border-radius: 8px !important;
    }
    input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 500 !important;
    }

    /* 5. Cards de Remédios e Consultas */
    .med-card {
        background-color: #FFFFFF !important;
        border: 2px solid #D0D0D0 !important;
        border-radius: 10px !important;
        padding: 20px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important;
    }
    
    /* 6. Caixas Expansíveis (Aba de Repor) */
    .streamlit-expanderHeader {
        background-color: #E9ECEF !important;
        border: 1px solid #D0D0D0 !important;
        border-radius: 8px !important;
    }
    .streamlit-expanderHeader * {
        color: #000000 !important;
    }
    div[data-testid="stExpanderDetails"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D0D0D0 !important;
        border-top: none !important;
    }

    /* 7. Botões (Exceção: Fundo Azul com Letra Branca para destaque) */
    div[data-testid="stButton"] > button {
        background-color: #0056B3 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
    }
    div[data-testid="stButton"] > button * {
        color: #FFFFFF !important; 
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #004494 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ALERTA DE ACESSO ---
if "acesso_notificado" not in st.session_state:
    enviar_telegram("🌐 App de Saúde foi acessado.")
    st.session_state.acesso_notificado = True

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2>🏥 Menu Saúde</h2>", unsafe_allow_html=True)
    if "admin" not in st.session_state: st.session_state.admin = False
    
    if not st.session_state.admin:
        pw = st.text_input("Senha ADM", type="password")
        if pw == SENHA_ADM: 
            st.session_state.admin = True
            st.rerun()
    else:
        st.success("✅ Logado como ADM")
        if st.button("Sair da Conta"):
            st.session_state.admin = False
            st.rerun()
    
    st.markdown("---")
    menu = st.radio("Navegação", ["📊 Estoque", "🩺 Consultas", "💰 Financeiro", "➕ Cadastro", "🗑️ Remover"])

# --- 5. TELAS ---

if menu == "📊 Estoque":
    st.markdown("<h1>💊 Controle de Estoque</h1>", unsafe_allow_html=True)
    df = api_get("remedios")
    if df.empty:
        st.info("Nenhum remédio cadastrado.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            dias_passados = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_passados * r['dose_diaria'])))
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)
            
            # Alertas Visuais Coloridos
            if dias_restantes < 7: cor, label = "#DC3545", "🚨 CRÍTICO"
            elif dias_restantes < 15: cor, label = "#FD7E14", "⚠️ ATENÇÃO"
            else: cor, label = "#198754", "✅ BOM"
            
            st.markdown(f"""
                <div class="med-card" style="border-left: 10px solid {cor} !important;">
                    <div style="float:right; background-color:{cor}; color:white; padding:4px 10px; border-radius:15px; font-weight:bold; font-size:12px;">{label}</div>
                    <h2 style="margin-top:0;">{r['nome'].upper()}</h2>
                    <p style="font-size: 16px;">📦 <b>Estoque:</b> {estoque_atual} un.<br>
                    📅 <b>Acaba em:</b> <span style="color:{cor}; font-weight:bold;">{data_fim.strftime('%d/%m/%Y')}</span></p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.admin:
                with st.expander(f"📥 Repor {r['nome']}"):
                    col1, col2 = st.columns(2)
                    n_q = col1.number_input("Qtd Nova", 1, 1000, 30, key=f"q_{r['id']}")
                    n_v = col2.number_input("Preço Total R$", 0.0, 10000.0, float(r['preco']), key=f"v_{r['id']}")
                    if st.button(f"Confirmar Reposição", key=f"btn_{r['id']}"):
                        nova_qtd = estoque_atual + n_q
                        requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(nova_qtd), "data_inicio": str(hoje.date()), "preco": float(n_v)})
                        requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(n_v), "data_compra": str(hoje.date())})
                        enviar_telegram(f"✅ Reposição Realizada!\nRemédio: {r['nome']}\nAdicionado: {n_q} un.\nTotal agora: {nova_qtd} un.")
                        st.success("Estoque atualizado!"); time.sleep(1); st.rerun()

elif menu == "🗑️ Remover":
    st.markdown("<h1>🗑️ Excluir Registros</h1>", unsafe_allow_html=True)
    if not st.session_state.admin: st.warning("🔒 Área Restrita para ADM.")
    else:
        tipo = st.selectbox("O que deseja excluir?", ["Remédio", "Consulta", "Compra Financeira"])
        tab = {"Remédio":"remedios", "Consulta":"consultas", "Compra Financeira":"compras"}[tipo]
        df_d = api_get(tab)
        
        if not df_d.empty:
            col_nome = 'nome' if tab == 'remedios' else 'medico' if tab == 'consultas' else 'nome_remedio'
            item = st.selectbox("Selecione o registro para APAGAR:", df_d[col_nome].tolist())
            id_item = df_d[df_d[col_nome] == item]['id'].values[0]
            
            if st.button("❌ APAGAR DEFINITIVAMENTE"):
                requests.delete(f"{URL_SUPABASE}{tab}?id=eq.{id_item}", headers=HEADERS)
                enviar_telegram(f"🗑️ Registro Removido: {item} (Tipo: {tipo})")
                st.success("Registro apagado com sucesso!"); time.sleep(1); st.rerun()
        else:
            st.info("Nenhum dado disponível para excluir.")

elif menu == "💰 Financeiro":
    st.markdown("<h1>💰 Resumo Financeiro</h1>", unsafe_allow_html=True)
    df_r, df_c = api_get("compras"), api_get("consultas")
    t1 = df_r['valor'].sum() if not df_r.empty else 0
    t2 = df_c['valor'].sum() if not df_c.empty else 0
    
    st.markdown(f"<h2>Total Gasto: <span style='color:#DC3545;'>R$ {t1+t2:.2f}</span></h2>", unsafe_allow_html=True)
    
    if not df_r.empty: 
        st.markdown("<h3>Detalhes das Compras</h3>", unsafe_allow_html=True)
        st.dataframe(df_r[['data_compra', 'nome_remedio', 'valor']], use_container_width=True)

elif menu == "➕ Cadastro":
    st.markdown("<h1>➕ Novo Cadastro</h1>", unsafe_allow_html=True)
    if not st.session_state.admin: st.warning("🔒 Área Restrita para ADM.")
    else:
        tipo_cad = st.selectbox("O que deseja cadastrar?", ["Remédio", "Consulta"])
        with st.form("cadastro_form"):
            if tipo_cad == "Remédio":
                n = st.text_input("Nome do Remédio")
                q = st.number_input("Quantidade Total na Caixa", 1)
                d = st.number_input("Dose por Dia (Ex: 1, 0.5, 2)", 0.1, 20.0, 1.0)
                p = st.number_input("Preço da Caixa R$", 0.0)
            else:
                n = st.text_input("Nome do Médico")
                p = st.number_input("Valor da Consulta R$", 0.0)
                
            if st.form_submit_button("Salvar Cadastro"):
                if tipo_cad == "Remédio":
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":n,"valor":float(p),"data_compra":str(datetime.now().date())})
                    enviar_telegram(f"🆕 NOVO REMÉDIO CADASTRADO: {n}")
                else:
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":n, "valor":float(p), "data_consulta":str(datetime.now().date())})
                st.success("Cadastro realizado com sucesso!"); time.sleep(1); st.rerun()

elif menu == "🩺 Consultas":
    st.markdown("<h1>🩺 Histórico Médico</h1>", unsafe_allow_html=True)
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            st.markdown(f"""
                <div class="med-card" style="border-left: 10px solid #0D6EFD !important;">
                    <h3 style="margin-top:0;">{c["data_consulta"].strftime("%d/%m/%Y")}</h3>
                    <p style="font-size: 16px;">👨‍⚕️ <b>Dr(a).</b> {c["medico"]}<br>
                    💵 <b>Valor:</b> R$ {c["valor"]:.2f}</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma consulta registrada.")
