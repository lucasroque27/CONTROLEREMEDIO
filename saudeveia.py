import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import time

# --- 1. CONFIGURAÇÕES (SUPABASE E TELEGRAM) ---
URL_SUPABASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"

TOKEN_TELEGRAM = "8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM"
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

# --- 3. ESTILO CSS (NOVO VISUAL "CLEAN" - AZUL CLARINHO) ---
st.set_page_config(page_title="Saúde Família", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    /* FUNDO DO APP TOTALMENTE BRANCO */
    .stApp { background-color: #FFFFFF !important; }

    /* MENU LATERAL (SIDEBAR) - AZUL BEM CLARINHO */
    [data-testid="stSidebar"] {
        background-color: #E6F0FF !important; /* Azul clarinho */
        border-right: 1px solid #C2D6F0; /* Borda suave */
    }
    
    /* FORÇA LETRA PRETA NO MENU (PARA VISIBILIDADE) */
    [data-testid="stSidebar"] * {
        color: #000000 !important;
        font-weight: 600;
    }

    /* BOTÃO DE MENU (HEADER) */
    header[data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
        visibility: visible !important;
    }

    /* CARDS DE REMÉDIO NA TELA PRINCIPAL */
    .med-card {
        background-color: #F8F9FA !important; /* Cinza muito claro */
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #E2E8F0;
        border-left: 12px solid #3B82F6; /* Borda de destaque azul */
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }

    /* TEXTO NA TELA PRINCIPAL (SEMPRE PRETO) */
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label, .stMarkdown {
        color: #000000 !important;
        font-weight: 600;
    }

    /* BOTÕES PREENCHIDOS DE AZUL */
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        background-color: #3B82F6 !important;
        color: white !important;
        font-weight: bold;
        height: 3em;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: black !important;'>Gestão Saúde</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    if "admin" not in st.session_state: st.session_state.admin = False
    
    if not st.session_state.admin:
        st.markdown("🔒 **Acesso ADM**")
        pw = st.text_input("Senha", type="password")
        if st.button("Liberar"):
            if pw == SENHA_ADM:
                st.session_state.admin = True
                st.rerun()
            else: st.error("Senha Incorreta")
    else:
        st.success("✨ Modo Editor Ativo")
        if st.button("Sair do Modo ADM"):
            st.session_state.admin = False
            st.rerun()
    
    st.markdown("---")
    # Menu com fundo claro e letra preta
    menu = st.radio("Navegação", ["📊 Estoque", "🩺 Consultas", "💰 Financeiro", "➕ Cadastro", "🗑️ Remover"])

# --- 5. LÓGICA DAS TELAS (MANTIDA) ---

if menu == "📊 Estoque":
    st.title("💊 Controle de Remédios")
    df = api_get("remedios")
    if df.empty:
        st.info("Nenhum remédio cadastrado.")
    else:
        hoje = datetime.now()
        if "alertas_enviados" not in st.session_state:
            st.session_state.alertas_enviados = []

        for _, r in df.iterrows():
            dias_passados = (hoje - r['data_inicio']).days
            consumo_real = dias_passados * r['dose_diaria']
            estoque_atual = max(0, int(r['qtd_total'] - consumo_real))
            
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)
            
            # ALERTA DE 7 DIAS
            if dias_restantes < 7 and r['nome'] not in st.session_state.alertas_enviados:
                msg = f"⚠️ ALERTA DE ESTOQUE: {r['nome']}\nAcaba em {dias_restantes} dias ({data_fim.strftime('%d/%m/%Y')})"
                enviar_telegram(msg)
                st.session_state.alertas_enviados.append(r['nome'])

            st.markdown(f"""
                <div class="med-card">
                    <span style="font-size: 1.4em;"><b>{r['nome'].upper()}</b></span><br><br>
                    <p style="margin:0; font-size: 1.1em;">📦 Restam: <b>{estoque_atual} comprimidos</b></p>
                    <p style="margin:0;">🕒 Dose diária: <b>{r['dose_diaria']} un.</b></p>
                    <p style="margin-top:10px; font-size: 1.2em; color: {'#CC0000' if dias_restantes < 7 else '#006600'} !important;">
                        📅 Acaba em: <b>{data_fim.strftime('%d/%m/%Y')}</b> ({dias_restantes} dias)
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.admin:
                with st.expander(f"🔄 Repor {r['nome']}"):
                    with st.form(f"form_{r['id']}"):
                        n_qtd = st.number_input("Quantidade comprada agora", min_value=1, value=30)
                        n_valor = st.number_input("Preço pago nesta caixa (R$)", min_value=0.0, value=float(r['preco']))
                        if st.form_submit_button("Confirmar Reposição"):
                            total_novo = estoque_atual + n_qtd
                            requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(total_novo), "data_inicio": str(hoje.date()), "preco": float(n_valor)})
                            requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(n_valor), "data_compra": str(hoje.date())})
                            enviar_telegram(f"✅ REPOSIÇÃO REALIZADA: {r['nome']}\n📦 Novo total: {total_novo} un.")
                            st.success("Atualizado!"); time.sleep(1); st.cache_data.clear(); st.rerun()

elif menu == "🩺 Consultas":
    st.title("🩺 Histórico de Consultas")
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            st.markdown(f"""
                <div class="med-card" style="border-left-color: #10B981;">
                    <p style="margin:0;">📅 Data: {c['data_consulta'].strftime('%d/%m/%Y')}</p>
                    <p style="margin:0; font-size: 1.2em;"><b>Dr(a). {c['medico']}</b></p>
                    <p style="margin:0; color: #166534;">Valor: R$ {float(c.get('valor', 0)):.2f}</p>
                </div>
            """, unsafe_allow_html=True)

elif menu == "💰 Financeiro":
    st.title("💰 Controle Financeiro")
    df_r, df_c = api_get("compras"), api_get("consultas")
    t1 = df_r['valor'].sum() if not df_r.empty else 0
    t2 = df_c['valor'].sum() if not df_c.empty else 0
    st.metric("Total Gasto", f"R$ {t1+t2:.2f}")
    if not df_r.empty:
        st.subheader("🛒 Compras de Remédios")
        st.dataframe(df_r[['data_compra', 'nome_remedio', 'valor']], use_container_width=True)

elif menu == "➕ Cadastro":
    if not st.session_state.admin: st.warning("Acesse modo ADM")
    else:
        tipo = st.selectbox("O que cadastrar?", ["Remédio", "Consulta"])
        with st.form("cad_novo"):
            if tipo == "Remédio":
                n, q = st.text_input("Nome"), st.number_input("Qtd Caixa", value=30)
                d, p = st.number_input("Dose/dia", value=1.0), st.number_input("Preço", value=0.0)
                if st.form_submit_button("Salvar"):
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":n,"valor":float(p),"data_compra":str(datetime.now().date())})
                    st.success("OK!"); time.sleep(1); st.rerun()
            else:
                m, v, dt = st.text_input("Médico"), st.number_input("Valor", value=0.0), st.date_input("Data")
                if st.form_submit_button("Salvar"):
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    st.success("OK!"); time.sleep(1); st.rerun()

elif menu == "🗑️ Remover":
    if not st.session_state.admin: st.warning("Acesse modo ADM")
    else:
        tab = st.selectbox("Categoria", ["remedios", "consultas", "compras"])
        df_d = api_get(tab)
        if not df_d.empty:
            col = 'nome' if tab == 'remedios' else 'medico' if tab == 'consultas' else 'nome_remedio'
            it = st.selectbox("Item", df_d[col].tolist())
            if st.button("Remover Permanentemente"):
                requests.delete(f"{URL_SUPABASE}{tab}?id=eq.{df_d[df_d[col] == it]['id'].values[0]}", headers=HEADERS)
                st.rerun()
