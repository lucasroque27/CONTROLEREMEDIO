import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time

# --- CONFIGURAÇÃO ---
URL_BASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
HEADERS = {
    "apikey": API_KEY, 
    "Authorization": f"Bearer {API_KEY}", 
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

@st.cache_data(ttl=1)
def buscar_dados(tabela):
    try:
        res = requests.get(f"{URL_BASE}{tabela}?select=*", headers=HEADERS)
        return pd.DataFrame(res.json())
    except: return pd.DataFrame()

# --- INTERFACE ---
st.set_page_config(page_title="SISTEMA SAUDE", layout="wide")
st.title("💊 Gestão de Medicamentos")

if "adm" not in st.session_state: st.session_state.adm = False

with st.sidebar:
    senha = st.text_input("Senha ADM", type="password")
    if st.button("Entrar") or senha == "1234":
        st.session_state.adm = True
    if st.button("Sair"):
        st.session_state.adm = False
    
    aba = st.radio("Menu", ["Estoque", "Financeiro", "Cadastrar", "Remover"])

# --- LOGICA ---

if aba == "Estoque":
    df = buscar_dados("remedios")
    if not df.empty:
        hoje = datetime.now()
        for _, r in df.iterrows():
            # PILAR: Cálculo de dose fracionada e estoque
            ini = pd.to_datetime(r['data_inicio'])
            passados = (hoje - ini).days
            atual = max(0.0, float(r['qtd_total']) - (passados * float(r['dose_diaria'])))
            resta = float(atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                c1.write(f"**{r['nome']}**")
                c2.metric("Estoque Atual", f"{atual:g}")
                c3.write(f"Acaba em: {(hoje + timedelta(days=resta)).strftime('%Y-%m-%d')}")
                
                if st.session_state.adm:
                    with st.expander("Ajustar"):
                        v_add = st.number_input("Add Qtd", 0.0, key=f"a{r['id']}")
                        v_pre = st.number_input("Preço", 0.0, value=float(r['preco']), key=f"p{r['id']}")
                        if st.button("Salvar Ajuste", key=f"b{r['id']}"):
                            pay = {"qtd_total": float(atual + v_add), "data_inicio": hoje.strftime('%Y-%m-%d'), "preco": float(v_pre)}
                            requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, json=pay)
                            st.cache_data.clear()
                            st.rerun()

elif aba == "Financeiro":
    df_r = buscar_dados("remedios")
    df_c = buscar_dados("consultas")
    tr = df_r['preco'].sum() if not df_r.empty else 0
    tc = df_c['valor'].sum() if not df_c.empty else 0
    st.metric("Total Acumulado", f"R$ {tr + tc:,.2f}")
    if not df_r.empty: st.bar_chart(df_r, x="nome", y="preco")

elif aba == "Cadastrar":
    if st.session_state.adm:
        tipo = st.selectbox("Tipo", ["Remédio", "Consulta"])
        with st.form("cad"):
            if tipo == "Remédio":
                n = st.text_input("Nome")
                q = st.number_input("Qtd Inicial", 0.0)
                d = st.number_input("Dose Diária", 0.0)
                p = st.number_input("Preço", 0.0)
                if st.form_submit_button("SALVAR"):
                    payload = {"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "preco": float(p), "data_inicio": datetime.now().strftime('%Y-%m-%d')}
                    res = requests.post(f"{URL_BASE}remedios", headers=HEADERS, json=payload)
                    if res.status_code in [200, 201]: st.success("Salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                    else: st.error(f"Erro: {res.text}")
            else:
                m = st.text_input("Médico")
                v = st.number_input("Valor", 0.0)
                if st.form_submit_button("SALVAR"):
                    payload = {"medico": m, "valor": float(v), "data_consulta": datetime.now().strftime('%Y-%m-%d')}
                    requests.post(f"{URL_BASE}consultas", headers=HEADERS, json=payload)
                    st.success("Salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()

elif aba == "Remover":
    if st.session_state.adm:
        t = st.selectbox("Tabela", ["remedios", "consultas"])
        df_del = buscar_dados(t)
        if not df_del.empty:
            campo = 'nome' if t == 'remedios' else 'medico'
            item = st.selectbox("Item", df_del[campo].tolist())
            if st.button("EXCLUIR"):
                id_i = df_del[df_del[campo] == item]['id'].values[0]
                requests.delete(f"{URL_BASE}{t}?id=eq.{id_i}", headers=HEADERS)
                st.success("Removido!"); st.cache_data.clear(); time.sleep(1); st.rerun()
