import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURAÇÃO DE CONEXÃO E TELEGRAM ---
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
        # Seu Bot e Chat ID configurados
        requests.post(f"https://api.telegram.org/bot8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM/sendMessage", 
                      json={"chat_id": "5256921022", "text": msg}, timeout=5)
    except:
        pass

@st.cache_data(ttl=1)
def buscar_dados(tabela):
    try:
        response = requests.get(f"{URL_BASE}{tabela}?select=*", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- 2. INTERFACE ---
st.set_page_config(page_title="Gestão Saúde", layout="centered")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

with st.sidebar:
    st.header("🔑 Acesso")
    if not st.session_state.autenticado:
        senha = st.text_input("Senha ADM", type="password")
        if st.button("Entrar") or (senha == "1234"):
            if senha == "1234":
                st.session_state.autenticado = True
                st.rerun()
    else:
        if st.button("Sair do Modo ADM"):
            st.session_state.autenticado = False
            st.rerun()
    
    st.divider()
    aba = st.radio("Navegação", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"])

# --- 3. TELAS ---

if aba == "Estoque":
    st.subheader("📋 Status do Estoque")
    df = buscar_dados("remedios")
    if df.empty:
        st.info("Nenhum dado encontrado.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            data_ini = pd.to_datetime(r['data_inicio'])
            dias_corridos = (hoje - data_ini).days
            qtd_atual = max(0.0, float(r['qtd_total']) - (dias_corridos * float(r['dose_diaria'])))
            dias_restantes = float(qtd_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)
            
            with st.expander(f"💊 {r['nome'].upper()}", expanded=True):
                c1, c2 = st.columns(2)
                c1.metric("Estoque", f"{qtd_atual:g}")
                c2.metric("Acaba em", data_fim.strftime('%Y-%m-%d'))
                
                if st.session_state.autenticado:
                    v_add = st.number_input("Adicionar Qtd", 0.0, key=f"a_{r['id']}")
                    v_prc = st.number_input("Novo Preço R$", 0.0, value=float(r['preco']), key=f"p_{r['id']}")
                    if st.button("Salvar Ajuste", key=f"b_{r['id']}"):
                        pay = {"qtd_total": float(qtd_atual + v_add), "data_inicio": hoje.strftime('%Y-%m-%d'), "preco": float(v_prc)}
                        res = requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, json=pay)
                        if res.status_code in [200, 204]:
                            enviar_telegram(f"✅ Estoque atualizado: {r['nome']} (+{v_add} unidades)")
                            st.cache_data.clear(); time.sleep(0.5); st.rerun()

elif aba == "Financeiro":
    st.subheader("💰 Resumo de Gastos")
    df_r = buscar_dados("remedios")
    df_c = buscar_dados("consultas")
    tot_r = df_r['preco'].sum() if not df_r.empty else 0
    tot_c = df_c['valor'].sum() if not df_c.empty else 0
    col1, col2 = st.columns(2)
    col1.metric("Total em Remédios", f"R$ {tot_r:,.2f}")
    col2.metric("Total em Consultas", f"R$ {tot_c:,.2f}")
    st.divider()
    st.metric("INVESTIMENTO TOTAL", f"R$ {tot_r + tot_c:,.2f}")

elif aba == "Consultas":
    st.subheader("🩺 Histórico")
    df = buscar_dados("consultas")
    if not df.empty:
        st.dataframe(df[['data_consulta', 'medico', 'valor']], use_container_width=True)

elif aba == "Cadastrar":
    if not st.session_state.autenticado:
        st.warning("Acesse com a senha na barra lateral.")
    else:
        tipo = st.selectbox("O que cadastrar?", ["Remédio", "Consulta"])
        with st.form("cad"):
            if tipo == "Remédio":
                n, q, d, p = st.text_input("Nome"), st.number_input("Qtd"), st.number_input("Dose/Dia"), st.number_input("Preço")
                if st.form_submit_button("SALVAR"):
                    pay = {"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "preco": float(p), "data_inicio": datetime.now().strftime('%Y-%m-%d')}
                    r = requests.post(f"{URL_BASE}remedios", headers=HEADERS, json=pay)
                    if r.status_code in [200, 201]:
                        enviar_telegram(f"🆕 Novo Remédio Cadastrado: {n}")
                        st.cache_data.clear(); time.sleep(0.5); st.rerun()
            else:
                m, v = st.text_input("Médico"), st.number_input("Valor")
                if st.form_submit_button("SALVAR"):
                    pay = {"medico": m, "valor": float(v), "data_consulta": datetime.now().strftime('%Y-%m-%d')}
                    requests.post(f"{URL_BASE}consultas", headers=HEADERS, json=pay)
                    st.cache_data.clear(); time.sleep(0.5); st.rerun()

elif aba == "Remover":
    if not st.session_state.autenticado:
        st.warning("Acesse com a senha.")
    else:
        tabela = st.selectbox("Categoria", ["remedios", "consultas"])
        df_del = buscar_dados(tabela)
        if not df_del.empty:
            campo = "nome" if tabela == "remedios" else "medico"
            item = st.selectbox("Selecione o item", df_del[campo].tolist())
            if st.button("🗑️ EXCLUIR"):
                id_item = df_del[df_del[campo] == item]['id'].values[0]
                requests.delete(f"{URL_BASE}{tabela}?id=eq.{id_item}", headers=HEADERS)
                st.cache_data.clear(); time.sleep(0.5); st.rerun()
