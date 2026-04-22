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

# --- 3. ESTILO CSS (ALTO CONTRASTE) ---
st.set_page_config(page_title="Saúde Família", page_icon="💊", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    [data-testid="stSidebar"] { background-color: #0A192F !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    header[data-testid="stHeader"] { background-color: white !important; }
    
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
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🏥 Gestão Saúde</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    if "admin" not in st.session_state: st.session_state.admin = False
    if not st.session_state.admin:
        pw = st.text_input("Senha ADM", type="password")
        if st.button("Liberar"):
            if pw == "1234": st.session_state.admin = True; st.rerun()
    else:
        st.success("✨ Modo Edição Ativo")
        if st.button("Sair ADM"): st.session_state.admin = False; st.rerun()

    st.markdown("---")
    menu = st.radio("Navegação", ["📊 Estoque", "🩺 Histórico Médico", "💰 Financeiro", "➕ Cadastro", "🗑️ Remover"])

# --- 5. LÓGICA PRINCIPAL ---
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
            estoque_atual = max(0, int(r['qtd_total'] - (dias_passados * r['dose_diaria'])))
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)

            # VIGIA DE 7 DIAS (DISPARA AUTOMÁTICO AO ABRIR O ESTOQUE)
            if dias_restantes < 7 and r['nome'] not in st.session_state.alertas_enviados:
                msg = f"⚠️ ALERTA: {r['nome']} ACABANDO!\n\nEstoque: {estoque_atual} un.\nDura apenas mais {dias_restantes} dias.\nAcaba em: {data_fim.strftime('%d/%m/%Y')}"
                enviar_telegram(msg)
                st.session_state.alertas_enviados.append(r['nome'])

            st.markdown(f"""
                <div class="med-card">
                    <span style="font-size: 1.4em;"><b>{r['nome'].upper()}</b></span><br>
                    <p>📦 Estoque: <b>{estoque_atual} un.</b> | 🕒 Dose: <b>{r['dose_diaria']} p/ dia</b></p>
                    <p style="font-size: 1.2em; color: {'#CC0000' if dias_restantes < 7 else '#006600'} !important;">
                        📅 Acaba em: <b>{data_fim.strftime('%d/%m/%Y')}</b> ({dias_restantes} dias)
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.admin:
                with st.expander(f"🔄 Repor {r['nome']}"):
                    with st.form(f"f_{r['id']}"):
                        n_qtd = st.number_input("Qtd comprada agora", min_value=1, value=30)
                        n_val = st.number_input("Preço da nova caixa", min_value=0.0, value=float(r['preco']))
                        if st.form_submit_button("Confirmar Reposição"):
                            total_novo = estoque_atual + n_qtd
                            requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(total_novo), "data_inicio": str(hoje.date()), "preco": float(n_val)})
                            requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(n_val), "data_compra": str(hoje.date())})
                            enviar_telegram(f"✅ REPOSIÇÃO: {r['nome']}\n📦 Novo total: {total_novo} un.\n💰 Valor: R$ {n_val:.2f}")
                            st.success("Atualizado!"); time.sleep(1); st.cache_data.clear(); st.rerun()

elif menu == "🩺 Histórico Médico":
    st.title("🩺 Consultas Realizadas")
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            st.markdown(f"""<div class="med-card"><b>{c['data_consulta'].strftime('%d/%m/%Y')}</b><br>Dr. {c['medico']}<br>R$ {float(c.get('valor', 0)):.2f}</div>""", unsafe_allow_html=True)

elif menu == "💰 Financeiro":
    st.title("💰 Resumo Financeiro")
    df_r = api_get("compras")
    df_c = api_get("consultas")
    t1 = df_r['valor'].sum() if not df_r.empty else 0
    t2 = df_c['valor'].sum() if not df_c.empty else 0
    st.metric("Gasto Total", f"R$ {t1+t2:.2f}")
    if not df_r.empty:
        st.subheader("🛒 Compras de Medicamentos")
        st.dataframe(df_r[['data_compra', 'nome_remedio', 'valor']], use_container_width=True)

elif menu == "➕ Cadastro":
    if not st.session_state.admin: st.warning("Acesse modo ADM")
    else:
        tipo = st.selectbox("Tipo de Cadastro:", ["Remédio", "Consulta"])
        with st.form("c_novo"):
            if tipo == "Remédio":
                n, q = st.text_input("Nome"), st.number_input("Qtd Caixa", value=30)
                d, p = st.number_input("Dose diária", value=1.0), st.number_input("Preço", value=0.0)
                if st.form_submit_button("Salvar Medicamento"):
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":n,"valor":float(p),"data_compra":str(datetime.now().date())})
                    enviar_telegram(f"🆕 NOVO MEDICAMENTO: {n}\n📦 {q} unidades")
                    st.success("Salvo!"); time.sleep(1); st.cache_data.clear(); st.rerun()
            else:
                m, v, dt_sel = st.text_input("Médico"), st.number_input("Valor"), st.date_input("Data")
                if st.form_submit_button("Salvar Consulta"):
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":m, "valor":float(v), "data_consulta":str(dt_sel)})
                    enviar_telegram(f"🩺 NOVA CONSULTA: {m}\n💰 Valor: R$ {v}")
                    st.success("Salvo!"); time.sleep(1); st.cache_data.clear(); st.rerun()

elif menu == "🗑️ Remover":
    if not st.session_state.admin: st.warning("Acesse modo ADM")
    else:
        tab = st.selectbox("Escolha a Categoria:", ["remedios", "consultas", "compras"])
        df_d = api_get(tab)
        if not df_d.empty:
            col = 'nome' if tab == 'remedios' else 'medico' if tab == 'consultas' else 'nome_remedio'
            it = st.selectbox("Item para Excluir:", df_d[col].tolist())
            if st.button("Remover Permanente"):
                requests.delete(f"{URL_SUPABASE}{tab}?id=eq.{df_d[df_d[col] == it]['id'].values[0]}", headers=HEADERS)
                st.success("Removido!"); time.sleep(1); st.cache_data.clear(); st.rerun()
