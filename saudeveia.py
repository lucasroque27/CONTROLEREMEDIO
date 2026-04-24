import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

# --- 1. CONFIGURAÇÕES ---
URL_SUPABASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
TOKEN_TELEGRAM = "8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM"
CHAT_ID = "5256921022"

HEADERS = {"apikey": API_KEY, "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}

# FUNÇÃO DE TELEGRAM PROTEGIDA
def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}, timeout=3)
    except:
        pass 

# CACHE DE DADOS (Estabilidade)
@st.cache_data(ttl=300)
def api_get(tabela):
    try:
        res = requests.get(f"{URL_SUPABASE}{tabela}?select=*&order=id.desc", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            for col in ['data_inicio', 'data_consulta', 'data_compra']:
                if not df.empty and col in df.columns: df[col] = pd.to_datetime(df[col])
            return df
    except:
        pass
    return pd.DataFrame()

# --- 2. ESTILO VISUAL ---
st.set_page_config(page_title="Gestão de Saúde", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f4f6f9; }
    header { background-color: transparent !important; }
    .block-container { padding-top: 1.5rem !important; }
    .card-remedio {
        background-color: white; border-radius: 12px; padding: 20px 25px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02); margin-bottom: 5px;
        margin-top: 15px; border: 1px solid #eef0f5;
    }
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
    .remedio-title { font-size: 20px; font-weight: 800; color: #2c3e50; margin: 0; text-transform: uppercase; }
    .badge-ok { background-color: #1dd1a1; color: white; padding: 5px 15px; border-radius: 20px; font-size: 11px; font-weight: bold; }
    .badge-alerta { background-color: #feca57; color: #2c3e50; padding: 5px 15px; border-radius: 20px; font-size: 11px; font-weight: bold; }
    .badge-repor { background-color: #ff6b6b; color: white; padding: 5px 15px; border-radius: 20px; font-size: 11px; font-weight: bold; }
    .preco { color: #10ac84; font-size: 13px; font-weight: 600; margin-bottom: 20px; }
    .grid-stats { display: flex; justify-content: space-between; text-align: center; border-top: 1px solid #f1f2f6; padding-top: 15px; }
    .stat-box { flex: 1; }
    .stat-box:not(:last-child) { border-right: 1px solid #f1f2f6; }
    .stat-num { font-size: 18px; font-weight: 800; color: #2c3e50; margin: 0; }
    .stat-label { font-size: 11px; color: #7f8c8d; margin: 0; margin-top: 4px; }
    </style>
    """, unsafe_allow_html=True)

# ALERTA INICIAL
if "first_run" not in st.session_state:
    enviar_telegram("🚀 **Sistema Online:** Rock, o painel de saúde foi acessado.")
    st.session_state.first_run = True

# --- 3. MENU LATERAL (CORRIGIDO PARA MOBILE) ---
with st.sidebar:
    st.title("🛡️ Gestão")
    if "admin" not in st.session_state: st.session_state.admin = False
    
    if not st.session_state.admin:
        pw = st.text_input("Senha Administrativa", type="password", key="login_pw")
        if st.button("Acessar Painel", use_container_width=True, key="btn_login"):
            if pw == "1234":
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
    else:
        st.success("Modo Administrador")
        if st.button("Sair do Modo ADM", use_container_width=True, key="btn_logout"): 
            st.session_state.admin = False
            st.rerun()
            
    # Key 'main_nav' evita o erro de DuplicateElementId
    aba = st.radio("Navegação:", ["Estoque", "Consultas", "Financeiro", "Cadastrar", "Remover"], key="main_nav")

meses_pt = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}

# --- 4. TELAS ---
if aba == "Estoque":
    st.markdown("<h2>📋 Resumo de Medicamentos</h2>", unsafe_allow_html=True)
    df = api_get("remedios")
    if not df.empty:
        hoje = datetime.now()
        itens_criticos = []
        for _, r in df.iterrows():
            dias_p = (hoje - r['data_inicio']).days
            estoque = max(0, int(r['qtd_total'] - (dias_p * r['dose_diaria'])))
            dias_r = int(estoque / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_f = hoje + timedelta(days=dias_r)
            
            badge = "badge-ok" if dias_r >= 15 else ("badge-alerta" if dias_r >= 7 else "badge-repor")
            txt_badge = "ESTOQUE BOM" if dias_r >= 15 else ("ATENÇÃO" if dias_r >= 7 else "REPOR")
            if dias_r < 7: itens_criticos.append(f"🔴 {r['nome']} ({dias_r} dias)")

            st.markdown(f"""
            <div class="card-remedio">
                <div class="card-header"><p class="remedio-title">💊 {r['nome']}</p><span class="{badge}">{txt_badge}</span></div>
                <div class="preco">💰 Preço da última compra: R$ {r['preco']:.2f}</div>
                <div class="grid-stats">
                    <div class="stat-box"><p class="stat-num">{estoque} un.</p><p class="stat-label">Quantidade</p></div>
                    <div class="stat-box"><p class="stat-num">{r['dose_diaria']}</p><p class="stat-label">Dose Diária</p></div>
                    <div class="stat-box"><p class="stat-num">{dias_r}</p><p class="stat-label">Dias de Dose</p></div>
                    <div class="stat-box"><p class="stat-num">{data_f.day}/{meses_pt[data_f.month]}</p><p class="stat-label">Acaba em</p></div>
                </div>
            </div>""", unsafe_allow_html=True)
            
            if st.session_state.admin:
                with st.expander(f"➕ Ajustar estoque/preço de {r['nome']}"):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    nq = c1.number_input("+ Adicionar Qtd", 1, 500, 30, key=f"q_{r['id']}")
                    np = c2.number_input("Novo Preço R$", 0.0, 5000.0, float(r['preco']), key=f"p_{r['id']}")
                    if c3.button("Salvar", key=f"btn_save_{r['id']}", use_container_width=True):
                        requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(estoque + nq), "data_inicio": str(hoje.date()), "preco": float(np)})
                        requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(np), "data_compra": str(hoje.date())})
                        st.cache_data.clear()
                        enviar_telegram(f"✅ **Reposição:** {r['nome']} atualizado para {int(estoque + nq)} unidades.")
                        st.rerun()

        if itens_criticos and "aviso_enviado" not in st.session_state:
            enviar_telegram("⚠️ **ALERTA DE ESTOQUE:**\n" + "\n".join(itens_criticos))
            st.session_state.aviso_enviado = True

elif aba == "Financeiro":
    st.markdown("<h2>💰 Controle Financeiro</h2>", unsafe_allow_html=True)
    df_r, df_c = api_get("compras"), api_get("consultas")
    t_r = df_r['valor'].sum() if not df_r.empty else 0
    t_c = df_c['valor'].sum() if not df_c.empty else 0
    st.metric("Total em Medicamentos", f"R$ {t_r:.2f}")
    st.metric("Total em Consultas", f"R$ {t_c:.2f}")
    if not df_r.empty:
        with st.expander("Ver Histórico de Compras"):
            st.dataframe(df_r[['data_compra', 'nome_remedio', 'valor']], use_container_width=True)

elif aba == "Consultas":
    st.markdown("<h2>🩺 Consultas Agendadas</h2>", unsafe_allow_html=True)
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            st.info(f"📅 **{c['data_consulta'].strftime('%d/%m/%Y')}** - {c['medico']} (R$ {c['valor']:.2f})")

elif aba == "Cadastrar":
    if st.session_state.admin:
        tipo = st.selectbox("Tipo de Cadastro", ["Remédio", "Consulta"], key="sel_cad")
        with st.form("form_novo"):
            if tipo == "Remédio":
                n = st.text_input("Nome")
                q = st.number_input("Quantidade", 1)
                d = st.number_input("Dose/Dia", 1.0)
                p = st.number_input("Preço", 0.0)
                if st.form_submit_button("Cadastrar"):
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    st.cache_data.clear()
                    enviar_telegram(f"🆕 **Novo Remédio:** {n} cadastrado.")
                    st.rerun()
            else:
                m = st.text_input("Médico")
                v = st.number_input("Valor")
                dt = st.date_input("Data")
                if st.form_submit_button("Cadastrar"):
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    st.cache_data.clear()
                    st.rerun()
    else:
        st.warning("Entre com a senha ADM para cadastrar.")

elif aba == "Remover":
    if st.session_state.admin:
        op = st.radio("Remover o quê?", ["Remédio", "Consulta"], key="radio_rem")
        df_rem = api_get("remedios" if op == "Remédio" else "consultas")
        if not df_rem.empty:
            lista = df_rem['nome'].tolist() if op == "Remédio" else df_rem['medico'].tolist()
            item = st.selectbox("Selecione para apagar", lista, key="sel_rem")
            if st.button("🗑️ Confirmar Exclusão", type="primary", use_container_width=True, key="btn_rem"):
                id_rem = df_rem[df_rem['nome' if op == "Remédio" else 'medico'] == item]['id'].values[0]
                requests.delete(f"{URL_SUPABASE}{'remedios' if op == 'Remédio' else 'consultas'}?id=eq.{id_rem}", headers=HEADERS)
                st.cache_data.clear()
                st.rerun()
    else:
        st.warning("Acesso restrito ao administrador.")
