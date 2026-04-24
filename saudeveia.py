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

# --- 3. ESTILO CSS "TOTAL CLARITY" (FORÇANDO CORES CLARAS) ---
st.set_page_config(page_title="Saúde Família", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    /* 1. Forçar fundo branco em tudo */
    .stApp, div[data-testid="stSidebar"], .main {
        background-color: #FFFFFF !important;
    }

    /* 2. Forçar fontes pretas e bem visíveis */
    h1, h2, h3, p, span, label, li, .stMarkdown {
        color: #000000 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }

    /* 3. Estilizar Inputs para não ficarem escuros */
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="number-input"] {
        background-color: #F0F2F6 !important;
        border: 2px solid #3B82F6 !important;
        border-radius: 10px !important;
    }
    
    input {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 500 !important;
    }

    /* 4. Botões de Ação (Azul Forte) */
    div.stButton > button {
        background-color: #1E40AF !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100% !important;
        border: none !important;
        padding: 10px !important;
    }

    /* 5. Estilo dos Cards de Remédio */
    .med-card {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 15px !important;
        padding: 20px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }

    /* 6. Corrigir Expander (A parte de 'Repor') */
    .streamlit-expanderHeader {
        background-color: #F8FAFC !important;
        color: #000000 !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }
    
    /* 7. Tabelas visíveis */
    .stDataFrame {
        border: 1px solid #CBD5E1 !important;
        background-color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Notificação de Acesso
if "acesso_notificado" not in st.session_state:
    enviar_telegram("🌐 App acessado.")
    st.session_state.acesso_notificado = True

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='color: black;'>🏥 Menu Saúde</h2>", unsafe_allow_html=True)
    if "admin" not in st.session_state: st.session_state.admin = False
    
    if not st.session_state.admin:
        pw = st.text_input("Senha", type="password")
        if pw == SENHA_ADM: 
            st.session_state.admin = True
            st.rerun()
    else:
        st.success("Modo Editor")
        if st.button("Sair"):
            st.session_state.admin = False
            st.rerun()
    
    menu = st.radio("Navegação", ["📊 Estoque", "🩺 Consultas", "💰 Financeiro", "➕ Cadastro", "🗑️ Remover"])

# --- 5. LÓGICA DE TELAS ---

if menu == "📊 Estoque":
    st.markdown("<h1>💊 Controle de Estoque</h1>", unsafe_allow_html=True)
    df = api_get("remedios")
    
    if df.empty:
        st.info("Lista vazia.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            dias_passados = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_passados * r['dose_diaria'])))
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)
            
            # Alertas
            if dias_restantes < 7: cor, label = "#EF4444", "🚨 CRÍTICO"
            elif dias_restantes < 15: cor, label = "#F59E0B", "⚠️ ATENÇÃO"
            else: cor, label = "#10B981", "✅ BOM"

            st.markdown(f"""
                <div class="med-card" style="border-left: 10px solid {cor};">
                    <div style="float:right; background:{cor}; color:white; padding:5px 12px; border-radius:20px; font-weight:bold;">{label}</div>
                    <h2 style="margin:0; color:black;">{r['nome'].upper()}</h2>
                    <p style="font-size:1.1em;">📦 Estoque: <b>{estoque_atual} un.</b> | 📅 Acaba em: <b>{data_fim.strftime('%d/%m/%Y')}</b></p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.admin:
                with st.expander(f"📥 Repor {r['nome']}"):
                    n_q = st.number_input(f"Qtd nova para {r['nome']}", 1, 1000, 30)
                    n_v = st.number_input(f"Preço de {r['nome']}", 0.0, 5000.0, float(r['preco']))
                    if st.button(f"Confirmar {r['nome']}"):
                        nova_qtd = estoque_atual + n_q
                        requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(nova_qtd), "data_inicio": str(hoje.date()), "preco": float(n_v)})
                        requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(n_v), "data_compra": str(hoje.date())})
                        enviar_telegram(f"✅ Reposição: {r['nome']}")
                        st.success("Atualizado!"); time.sleep(1); st.rerun()

elif menu == "🗑️ Remover":
    st.markdown("<h1>🗑️ Excluir Registros</h1>", unsafe_allow_html=True)
    if not st.session_state.admin: st.warning("Acesse como ADM.")
    else:
        tipo = st.selectbox("O que remover?", ["Remédio", "Consulta", "Compra"])
        tab_map = {"Remédio": "remedios", "Consulta": "consultas", "Compra": "compras"}
        tabela = tab_map[tipo]
        
        df_del = api_get(tabela)
        if not df_del.empty:
            col_n = 'nome' if tabela == 'remedios' else 'medico' if tabela == 'consultas' else 'nome_remedio'
            item = st.selectbox("Selecione o item:", df_del[col_n].tolist())
            id_i = df_del[df_del[col_n] == item]['id'].values[0]
            
            if st.button("Confirmar Exclusão"):
                requests.delete(f"{URL_SUPABASE}{tabela}?id=eq.{id_i}", headers=HEADERS)
                enviar_telegram(f"🗑️ Removido: {item}")
                st.success("Excluído com sucesso!"); time.sleep(1); st.rerun()

elif menu == "💰 Financeiro":
    st.markdown("<h1>💰 Resumo Financeiro</h1>", unsafe_allow_html=True)
    df_r = api_get("compras")
    df_c = api_get("consultas")
    total = (df_r['valor'].sum() if not df_r.empty else 0) + (df_c['valor'].sum() if not df_c.empty else 0)
    st.markdown(f"<h2>Total Gasto: R$ {total:.2f}</h2>", unsafe_allow_html=True)
    if not df_r.empty: st.write("### Detalhes"), st.dataframe(df_r[['data_compra', 'nome_remedio', 'valor']], use_container_width=True)

elif menu == "➕ Cadastro":
    if not st.session_state.admin: st.warning("Acesse como ADM.")
    else:
        cad = st.selectbox("Escolha:", ["Remédio", "Consulta"])
        with st.form("cad_form"):
            if cad == "Remédio":
                n, q, d, p = st.text_input("Nome"), st.number_input("Qtd", 1), st.number_input("Dose/dia", 1.0), st.number_input("Preço", 0.0)
            else:
                n, p = st.text_input("Médico"), st.number_input("Preço", 0.0)
            if st.form_submit_button("Salvar"):
                if cad == "Remédio":
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n, "qtd_total":int(q), "dose_diaria":float(d), "preco":float(p), "data_inicio":str(datetime.now().date())})
                    requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":n, "valor":float(p), "data_compra":str(datetime.now().date())})
                else:
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":n, "valor":float(p), "data_consulta":str(datetime.now().date())})
                st.success("Salvo!"); time.sleep(1); st.rerun()

elif menu == "🩺 Consultas":
    st.markdown("<h1>🩺 Histórico Médico</h1>", unsafe_allow_html=True)
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            st.markdown(f'<div class="med-card"><b>{c["data_consulta"].strftime("%d/%m/%Y")}</b> - Dr. {c["medico"]}<br>Valor: R$ {c["valor"]:.2f}</div>', unsafe_allow_html=True)
