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

# --- 3. ESTILO CSS (CORREÇÃO DE CORES ESCURAS) ---
st.set_page_config(page_title="Saúde Família", page_icon="💊", layout="centered")

# Alerta de acesso (MANTIDO)
if "acesso_notificado" not in st.session_state:
    enviar_telegram("🌐 Alerta: App de Saúde acessado!")
    st.session_state.acesso_notificado = True

st.markdown("""
    <style>
    /* Fundo e Textos Gerais */
    .stApp { background-color: #F8FAFC !important; }
    .stApp, p, span, label, h1, h2, h3 { color: #1E293B !important; }

    /* Correção de campos escuros (Inputs e Number Inputs) */
    div[data-baseweb="input"], div[data-baseweb="number-input"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }
    input { 
        color: #1E293B !important; 
        -webkit-text-fill-color: #1E293B !important;
    }

    /* Botões com melhor visibilidade */
    div.stButton > button {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        transition: 0.3s;
    }
    div.stButton > button:hover { background-color: #1D4ED8 !important; }

    /* Cards e Alertas */
    .med-card {
        background-color: #FFFFFF !important;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .status-badge { float: right; padding: 4px 12px; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.markdown("## 🏥 Gestão Saúde")
    if "admin" not in st.session_state: st.session_state.admin = False
    
    if not st.session_state.admin:
        pw = st.text_input("Acesso ADM", type="password")
        if pw == SENHA_ADM: 
            st.session_state.admin = True
            st.rerun()
    else:
        st.success("🔓 Modo Editor")
        if st.button("Encerrar Sessão"):
            st.session_state.admin = False
            st.rerun()
    
    menu = st.radio("Menu", ["📊 Estoque", "🩺 Consultas", "💰 Financeiro", "➕ Cadastro", "🗑️ Remover"])

# --- 5. TELAS ---

if menu == "📊 Estoque":
    st.title("📊 Controle de Estoque")
    df = api_get("remedios")
    if df.empty: st.info("Nenhum remédio cadastrado.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            dias_passados = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_passados * r['dose_diaria'])))
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)
            
            # Alertas Visuais e Telegram (PRESERVADOS)
            if dias_restantes < 7: cor, label = "#EF4444", "🚨 CRÍTICO"
            elif dias_restantes < 15: cor, label = "#F59E0B", "⚠️ ATENÇÃO"
            else: cor, label = "#10B981", "✅ BOM"

            st.markdown(f"""
                <div class="med-card" style="border-left: 8px solid {cor};">
                    <div class="status-badge" style="background-color: {cor};">{label}</div>
                    <h3 style="margin:0;">{r['nome'].upper()}</h3>
                    <p>📦 <b>{estoque_atual}</b> un. restantes | 📅 Acaba em: <b>{data_fim.strftime('%d/%m/%Y')}</b></p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.admin:
                with st.expander(f"Repor {r['nome']}"):
                    col1, col2 = st.columns(2)
                    n_q = col1.number_input("Qtd Nova", 1, 1000, 30, key=f"q_{r['id']}")
                    n_v = col2.number_input("Preço", 0.0, 50000.0, float(r['preco']), key=f"v_{r['id']}")
                    if st.button("Confirmar Reposição", key=f"btn_{r['id']}"):
                        nova_qtd = estoque_atual + n_q
                        requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(nova_qtd), "data_inicio": str(hoje.date()), "preco": float(n_v)})
                        requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(n_v), "data_compra": str(hoje.date())})
                        enviar_telegram(f"✅ Reposição: {r['nome']} (+{n_q} un.)")
                        st.success("Estoque atualizado!"); time.sleep(1); st.rerun()

elif menu == "🗑️ Remover":
    st.title("🗑️ Remover Registros")
    if not st.session_state.admin: st.warning("🔒 Área restrita para administradores.")
    else:
        tipo_del = st.selectbox("O que deseja remover?", ["Remédio", "Consulta", "Histórico de Compra"])
        tab_map = {"Remédio": "remedios", "Consulta": "consultas", "Histórico de Compra": "compras"}
        tabela = tab_map[tipo_del]
        
        df_del = api_get(tabela)
        if df_del.empty: st.info("Nada para remover.")
        else:
            # Identifica a coluna de nome baseada na tabela
            col_nome = 'nome' if tabela == 'remedios' else 'medico' if tabela == 'consultas' else 'nome_remedio'
            item_selecionado = st.selectbox("Selecione o item:", df_del[col_nome].tolist())
            id_item = df_del[df_del[col_nome] == item_selecionado]['id'].values[0]
            
            if st.button("❌ Confirmar Exclusão Definitiva"):
                res = requests.delete(f"{URL_SUPABASE}{tabela}?id=eq.{id_item}", headers=HEADERS)
                if res.status_code in [200, 204]:
                    enviar_telegram(f"🗑️ Registro Removido: {item_selecionado} ({tipo_del})")
                    st.success(f"Sucesso! {item_selecionado} foi removido.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Erro ao remover do banco de dados.")

# --- OUTRAS TELAS MANTIDAS E PROTEGIDAS ---
elif menu == "🩺 Consultas":
    st.title("🩺 Consultas")
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            st.markdown(f'<div class="med-card"><b>{c["data_consulta"].strftime("%d/%m/%Y")}</b> - Dr. {c["medico"]}<br>R$ {c["valor"]:.2f}</div>', unsafe_allow_html=True)

elif menu == "💰 Financeiro":
    st.title("💰 Resumo Financeiro")
    df_r = api_get("compras")
    df_c = api_get("consultas")
    total = (df_r['valor'].sum() if not df_r.empty else 0) + (df_c['valor'].sum() if not df_c.empty else 0)
    st.metric("Total Gasto", f"R$ {total:.2f}")
    if not df_r.empty: st.write("### Detalhes de Compras"), st.dataframe(df_r[['data_compra', 'nome_remedio', 'valor']], use_container_width=True)

elif menu == "➕ Cadastro":
    if not st.session_state.admin: st.warning("🔒 Área restrita.")
    else:
        cad = st.selectbox("Cadastrar:", ["Remédio", "Consulta"])
        with st.form("f_cad"):
            if cad == "Remédio":
                n = st.text_input("Nome")
                q = st.number_input("Qtd Inicial", 1, 1000, 30)
                d = st.number_input("Dose Diária", 0.1, 20.0, 1.0)
                p = st.number_input("Preço", 0.0)
                if st.form_submit_button("Salvar"):
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n, "qtd_total":int(q), "dose_diaria":float(d), "preco":float(p), "data_inicio":str(datetime.now().date())})
                    requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":n, "valor":float(p), "data_compra":str(datetime.now().date())})
                    st.success("Cadastrado!"); time.sleep(1); st.rerun()
            else:
                m = st.text_input("Médico")
                v = st.number_input("Valor", 0.0)
                dt = st.date_input("Data", datetime.now())
                if st.form_submit_button("Salvar"):
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    st.success("Consulta Salva!"); time.sleep(1); st.rerun()
