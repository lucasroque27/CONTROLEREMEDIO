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

HEADERS = {"apikey": API_KEY, "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}

# FUNÇÃO DE ENVIO MELHORADA COM FEEDBACK DE ERRO
def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            st.error(f"Erro Telegram: {response.text}") # Isso te ajuda a descobrir o porquê não chega
        return response.status_code == 200
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return False

def api_get(tabela):
    try:
        res = requests.get(f"{URL_SUPABASE}{tabela}?select=*&order=id.desc", headers=HEADERS)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            for col in ['data_inicio', 'data_consulta', 'data_compra']:
                if not df.empty and col in df.columns: df[col] = pd.to_datetime(df[col])
            return df
    except: pass
    return pd.DataFrame()

# --- 2. ESTILO ---
st.set_page_config(page_title="Saúde", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f4f6f9; }
    header { background-color: transparent !important; }
    .block-container { padding-top: 2rem !important; }
    .card-remedio {
        background-color: white; border-radius: 12px; padding: 20px 25px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04); margin-bottom: 5px;
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
    div[data-testid="stExpander"] { border-radius: 8px !important; margin-bottom: 15px; background-color: #fcfcfc;}
    </style>
    """, unsafe_allow_html=True)

# --- ALERTA DE ENTRADA IMEDIATO ---
if "log_entrada" not in st.session_state:
    if enviar_telegram("🚀 **Sistema Online:** Rock, o painel de saúde foi aberto agora."):
        st.session_state.log_entrada = True

# --- 3. MENU LATERAL ---
with st.sidebar:
    st.title("🛡️ Painel")
    if "admin" not in st.session_state: st.session_state.admin = False
    if not st.session_state.admin:
        pw = st.text_input("Senha ADM", type="password")
        if st.button("Acessar"):
            if pw == "1234": st.session_state.admin = True; st.rerun()
    else:
        if st.button("Sair"): st.session_state.admin = False; st.rerun()
    aba = st.radio("Menu", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"], label_visibility="collapsed")

meses_pt = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}

# --- 4. ESTOQUE ---
if aba == "Estoque":
    st.markdown("<h2>💊 Medicamentos</h2>", unsafe_allow_html=True)
    df = api_get("remedios")
    if not df.empty:
        hoje = datetime.now()
        itens_para_avisar = []

        for _, r in df.iterrows():
            dias_p = (hoje - r['data_inicio']).days
            estoque = max(0, int(r['qtd_total'] - (dias_p * r['dose_diaria'])))
            dias_r = int(estoque / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_f = hoje + timedelta(days=dias_r)
            
            # Lógica de badge
            badge = "badge-ok" if dias_r >= 15 else ("badge-alerta" if dias_r >= 7 else "badge-repor")
            txt_badge = "ESTOQUE OK" if dias_r >= 15 else ("ATENÇÃO" if dias_r >= 7 else "REPOR")

            # Coleta itens críticos para avisar no Telegram de uma vez só
            if dias_r < 7:
                itens_para_avisar.append(f"🔴 {r['nome']} ({dias_r} dias rest.)")

            st.markdown(f"""
            <div class="card-remedio">
                <div class="card-header"><p class="remedio-title">{r['nome']}</p><span class="{badge}">{txt_badge}</span></div>
                <div class="preco">$ Última Compra: R$ {r['preco']:.2f}</div>
                <div class="grid-stats">
                    <div class="stat-box"><p class="stat-num">{estoque}</p><p class="stat-label">Restantes</p></div>
                    <div class="stat-box"><p class="stat-num">{r['dose_diaria']}</p><p class="stat-label">Por Dia</p></div>
                    <div class="stat-box"><p class="stat-num">{dias_r}d</p><p class="stat-label">Duração</p></div>
                    <div class="stat-box"><p class="stat-num">{data_f.day}/{meses_pt[data_f.month]}</p><p class="stat-label">Fim</p></div>
                </div>
            </div>""", unsafe_allow_html=True)
            
            if st.session_state.admin:
                with st.expander(f"Ajustar {r['nome']}"):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    nq = c1.number_input("Qtd +", 1, 500, 30, key=f"q_{r['id']}")
                    np = c2.number_input("R$", 0.0, 5000.0, float(r['preco']), key=f"p_{r['id']}")
                    if c3.button("Salvar", key=f"b_{r['id']}"):
                        requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(estoque + nq), "data_inicio": str(hoje.date()), "preco": float(np)})
                        requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(np), "data_compra": str(hoje.date())})
                        enviar_telegram(f"✅ **Reposição:**\nRemédio: {r['nome']}\nNovo estoque: {int(estoque + nq)}")
                        st.rerun()

        # Envia resumo crítico se houver
        if itens_para_avisar and "aviso_estoque" not in st.session_state:
            resumo = "\n".join(itens_para_avisar)
            if enviar_telegram(f"⚠️ **ESTOQUE CRÍTICO:**\n{resumo}"):
                st.session_state.aviso_estoque = True

# --- ABAS FINANCEIRO E CONSULTAS (MANTIDAS IGUAIS) ---
elif aba == "Financeiro":
    st.markdown("<h2>💰 Financeiro</h2>", unsafe_allow_html=True)
    df_r, df_c = api_get("compras"), api_get("consultas")
    t_r = df_r['valor'].sum() if not df_r.empty else 0
    t_c = df_c['valor'].sum() if not df_c.empty else 0
    st.metric("💊 Remédios", f"R$ {t_r:.2f}")
    st.metric("🩺 Consultas", f"R$ {t_c:.2f}")
    st.success(f"**Total Geral: R$ {t_r + t_c:.2f}**")

elif aba == "Consultas":
    st.markdown("<h2>🩺 Consultas</h2>", unsafe_allow_html=True)
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            st.info(f"**{c['medico']}**\n{c['data_consulta'].strftime('%d/%m/%Y')} | R$ {c['valor']:.2f}")

elif aba == "Cadastrar":
    st.markdown("<h2>➕ Adicionar</h2>", unsafe_allow_html=True)
    if st.session_state.admin:
        tipo = st.selectbox("Tipo", ["Remédio", "Consulta"])
        with st.form("cad"):
            if tipo == "Remédio":
                n, q, d, p = st.text_input("Nome"), st.number_input("Qtd", 1), st.number_input("Dose", 1.0), st.number_input("Preço", 0.0)
                if st.form_submit_button("Salvar"):
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    enviar_telegram(f"🆕 **Novo Remédio:** {n}")
                    st.rerun()
            else:
                m, v, dt = st.text_input("Médico"), st.number_input("Valor"), st.date_input("Data")
                if st.form_submit_button("Salvar"):
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    enviar_telegram(f"🩺 **Nova Consulta:** {m} para o dia {dt}")
                    st.rerun()

elif aba == "Remover":
    st.markdown("<h2>🗑️ Remover</h2>", unsafe_allow_html=True)
    if st.session_state.admin:
        op = st.radio("O que remover?", ["Remédio", "Consulta"])
        if op == "Remédio":
            df_d = api_get("remedios")
            if not df_d.empty:
                it = st.selectbox("Remédio", df_d['nome'].tolist())
                if st.button("Excluir"):
                    requests.delete(f"{URL_SUPABASE}remedios?id=eq.{df_d[df_d['nome']==it]['id'].values[0]}", headers=HEADERS)
                    st.rerun()
        else:
            df_dc = api_get("consultas")
            if not df_dc.empty:
                lista = [f"{c['medico']} ({c['data_consulta'].strftime('%d/%m')})" for _, c in df_dc.iterrows()]
                it_c = st.selectbox("Consulta", lista)
                if st.button("Excluir"):
                    idx = lista.index(it_c)
                    requests.delete(f"{URL_SUPABASE}consultas?id=eq.{df_dc.iloc[idx]['id']}", headers=HEADERS)
                    st.rerun()
