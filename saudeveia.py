import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import time

# --- 1. CONEXÃO DIRETA E LIMPA ---
URL_BASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
HEADERS = {
    "apikey": API_KEY, 
    "Authorization": f"Bearer {API_KEY}", 
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def enviar_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM/sendMessage", 
                      json={"chat_id": "5256921022", "text": msg}, timeout=5)
    except: pass

@st.cache_data(ttl=2)
def buscar_dados(tabela):
    try:
        res = requests.get(f"{URL_BASE}{tabela}?select=*&order=id.desc", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            for col in ['data_inicio', 'data_consulta', 'data_compra']:
                if not df.empty and col in df.columns: 
                    df[col] = pd.to_datetime(df[col])
            return df
    except: pass
    return pd.DataFrame()

# --- 2. CONFIGURAÇÃO DE TELA ---
st.set_page_config(page_title="Gestão Saúde", layout="centered")
st.markdown("<style>.card { background: white; border-radius: 10px; padding: 15px; margin-bottom: 10px; border: 1px solid #eee; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }</style>", unsafe_allow_html=True)

if "admin" not in st.session_state: st.session_state.admin = False

with st.sidebar:
    st.title("💊 Menu Principal")
    if not st.session_state.admin:
        pw = st.text_input("Senha", type="password")
        if st.button("Entrar") or pw == "1234":
            if pw == "1234": st.session_state.admin = True; st.rerun()
    else:
        if st.button("Sair do ADM"): st.session_state.admin = False; st.rerun()
    
    aba = st.radio("Navegação:", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"])

# --- 3. FUNCIONALIDADES ---

if aba == "Estoque":
    st.subheader("📋 Estoque de Remédios")
    df = buscar_dados("remedios")
    if not df.empty:
        hoje = datetime.now()
        for _, r in df.iterrows():
            # Cálculo de pilar: Dias passados e estoque atual
            d_passados = (hoje - r['data_inicio']).days
            est_at = max(0.0, float(r['qtd_total']) - (d_passados * float(r['dose_diaria'])))
            d_restantes = float(est_at / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_f = hoje + timedelta(days=d_restantes)
            
            st.markdown(f"""<div class="card"><b>💊 {r['nome'].upper()}</b><br>
            Estoque: {est_at:g} | Dose/Dia: {r['dose_diaria']:g}<br>
            Previsão de término: {data_f.strftime('%d/%m/%Y')} ({int(d_restantes)} dias)</div>""", unsafe_allow_html=True)

            if st.session_state.admin:
                with st.expander(f"Ajustar {r['nome']}"):
                    v_add = st.number_input("Adicionar quantidade", 0.0, 10000.0, 0.0, key=f"a_{r['id']}")
                    v_prc = st.number_input("Preço Unitário R$", 0.0, 1000000.0, float(r['preco']), key=f"p_{r['id']}")
                    if st.button("Salvar Alterações", key=f"b_{r['id']}", use_container_width=True):
                        # Reset pilar: Nova data de início para reiniciar contagem
                        payload = {"qtd_total": float(est_at + v_add), "data_inicio": hoje.strftime('%Y-%m-%d'), "preco": float(v_prc)}
                        res = requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, json=payload)
                        if res.status_code in [200, 201, 204]:
                            requests.post(f"{URL_BASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(v_prc), "data_compra": hoje.strftime('%Y-%m-%d')})
                            st.success("Atualizado!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                        else: st.error("Erro ao salvar no banco.")

elif aba == "Financeiro":
    st.subheader("💰 Controle de Gastos")
    df_r, df_c = buscar_dados("remedios"), buscar_dados("consultas")
    t_r = df_r['preco'].sum() if not df_r.empty else 0
    t_c = df_c['valor'].sum() if not df_c.empty else 0
    
    col1, col2 = st.columns(2)
    col1.metric("Remédios", f"R$ {t_r:,.2f}")
    col2.metric("Consultas", f"R$ {t_c:,.2f}")
    
    gastos = []
    if not df_r.empty:
        temp = df_r[['data_inicio', 'preco']].rename(columns={'data_inicio': 'Data', 'preco': 'Valor'})
        temp['Tipo'] = 'Remédio'; gastos.append(temp)
    if not df_c.empty:
        temp = df_c[['data_consulta', 'valor']].rename(columns={'data_consulta': 'Data', 'valor': 'Valor'})
        temp['Tipo'] = 'Consulta'; gastos.append(temp)
    
    if gastos:
        df_f = pd.concat(gastos)
        df_f['Mês'] = df_f['Data'].dt.strftime('%m/%Y')
        st.bar_chart(df_f.groupby(['Mês', 'Tipo'])['Valor'].sum().reset_index(), x="Mês", y="Valor", color="Tipo")

elif aba == "Consultas":
    st.subheader("🩺 Histórico de Consultas")
    df = buscar_dados("consultas")
    if not df.empty:
        for _, c in df.iterrows():
            st.info(f"📅 {c['data_consulta'].strftime('%d/%m/%Y')} - {c['medico']} (R$ {float(c['valor']):,.2f})")

elif aba == "Cadastrar":
    if st.session_state.admin:
        op = st.radio("Novo cadastro:", ["Medicamento", "Consulta"])
        with st.form("cad_form", clear_on_submit=True):
            if op == "Medicamento":
                n = st.text_input("Nome")
                q = st.number_input("Qtd Inicial", 0.0)
                d = st.number_input("Dose Diária", 0.0)
                p = st.number_input("Preço", 0.0)
                if st.form_submit_button("CADASTRAR"):
                    if n and q > 0:
                        dat = {"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "preco": float(p), "data_inicio": datetime.now().strftime('%Y-%m-%d')}
                        r = requests.post(f"{URL_BASE}remedios", headers=HEADERS, json=dat)
                        if r.status_code in [200, 201, 204]:
                            enviar_telegram(f"Novo remédio: {n}"); st.success("Salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()
            else:
                m = st.text_input("Médico")
                v = st.number_input("Valor", 0.0)
                dt = st.date_input("Data")
                if st.form_submit_button("CADASTRAR"):
                    dat = {"medico": m, "valor": float(v), "data_consulta": dt.strftime('%Y-%m-%d')}
                    r = requests.post(f"{URL_BASE}consultas", headers=HEADERS, json=dat)
                    if r.status_code in [200, 201, 204]:
                        st.success("Salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()

elif aba == "Remover":
    if st.session_state.admin:
        tab = st.selectbox("Apagar de:", ["remedios", "consultas"])
        df_r = buscar_dados(tab)
        if not df_r.empty:
            col = 'nome' if tab == 'remedios' else 'medico'
            item = st.selectbox("Selecione o item:", df_r[col].tolist())
            if st.button("🗑️ APAGAR DEFINITIVAMENTE", type="primary"):
                idx = df_r[df_r[col] == item]['id'].values[0]
                r = requests.delete(f"{URL_BASE}{tab}?id=eq.{idx}", headers=HEADERS)
                if r.status_code in [200, 204]:
                    st.success("Removido!"); st.cache_data.clear(); time.sleep(1); st.rerun()
