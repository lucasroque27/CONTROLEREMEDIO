import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import time

# --- CONFIGURAÇÃO DE CONEXÃO (PADRÃO SUPABASE) ---
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

@st.cache_data(ttl=1)
def buscar_dados(tabela):
    try:
        res = requests.get(f"{URL_BASE}{tabela}?select=*&order=id.desc", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return pd.DataFrame(res.json())
    except: pass
    return pd.DataFrame()

# --- INTERFACE NATIVA STREAMLIT ---
st.set_page_config(page_title="Saude Controle", layout="centered")

if "admin" not in st.session_state: st.session_state.admin = False

with st.sidebar:
    st.title("💊 Gestão")
    if not st.session_state.admin:
        pw = st.text_input("Acesso", type="password")
        if st.button("Logar") or pw == "1234":
            if pw == "1234": st.session_state.admin = True; st.rerun()
    else:
        if st.button("Logoff"): st.session_state.admin = False; st.rerun()
    
    menu = st.radio("Navegar:", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"])

# --- FUNCIONALIDADES ---

if menu == "Estoque":
    st.subheader("📋 Status de Medicamentos")
    df = buscar_dados("remedios")
    if not df.empty:
        hoje = datetime.now()
        for _, r in df.iterrows():
            # Cálculos de Pilar (Doses Fracionadas e Datas)
            dt_ini = pd.to_datetime(r['data_inicio'])
            dias_passados = (hoje - dt_ini).days
            estoque_atual = max(0.0, float(r['qtd_total']) - (dias_passados * float(r['dose_diaria'])))
            dias_restantes = float(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)
            
            with st.expander(f"💊 {r['nome'].upper()}", expanded=True):
                col1, col2, col3 = st.columns(3)
                col1.metric("Estoque", f"{estoque_atual:g}")
                col2.metric("Dose/Dia", f"{r['dose_diaria']:g}")
                col3.metric("Dias", int(dias_restantes))
                st.write(f"Previsão de Término: **{data_fim.strftime('%Y-%m-%d')}**")
                
                if st.session_state.admin:
                    st.divider()
                    v_add = st.number_input("Adicionar Qtd", 0.0, key=f"add_{r['id']}")
                    v_prc = st.number_input("Preço Atual R$", 0.0, 1000000.0, float(r['preco']), key=f"prc_{r['id']}")
                    if st.button("Salvar Ajuste", key=f"btn_{r['id']}", use_container_width=True):
                        # Reset do pilar de contagem conforme padrão Supabase
                        pay = {
                            "qtd_total": float(estoque_atual + v_add), 
                            "data_inicio": hoje.strftime('%Y-%m-%d'), 
                            "preco": float(v_prc)
                        }
                        res = requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, json=pay)
                        if res.status_code in [200, 204]:
                            st.success("OK!"); st.cache_data.clear(); time.sleep(0.5); st.rerun()

elif menu == "Financeiro":
    st.subheader("💰 Controle de Gastos")
    df_r, df_c = buscar_dados("remedios"), buscar_dados("consultas")
    
    # Pilar: Financeiro Dinâmico
    tot_r = df_r['preco'].sum() if not df_r.empty else 0
    tot_c = df_c['valor'].sum() if not df_c.empty else 0
    
    st.metric("Total Geral Investido", f"R$ {tot_r + tot_c:,.2f}")
    
    if not df_r.empty or not df_c.empty:
        graf = []
        if not df_r.empty: graf.append(pd.DataFrame({'Categoria': 'Remédios', 'Custo': df_r['preco']}))
        if not df_c.empty: graf.append(pd.DataFrame({'Categoria': 'Consultas', 'Custo': df_c['valor']}))
        st.bar_chart(pd.concat(graf), x='Categoria', y='Custo')

elif menu == "Consultas":
    st.subheader("🩺 Histórico Médico")
    df = buscar_dados("consultas")
    if not df.empty:
        st.table(df[['data_consulta', 'medico', 'valor']])

elif menu == "Cadastrar":
    if st.session_state.admin:
        tipo = st.selectbox("O que cadastrar?", ["Remédio", "Consulta"])
        with st.form("main_cad"):
            if tipo == "Remédio":
                n = st.text_input("Nome")
                q = st.number_input("Qtd Inicial", 0.0)
                d = st.number_input("Dose Diária", 0.0)
                p = st.number_input("Preço R$", 0.0)
                if st.form_submit_button("CADASTRAR"):
                    pay = {"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "preco": float(p), "data_inicio": datetime.now().strftime('%Y-%m-%d')}
                    r = requests.post(f"{URL_BASE}remedios", headers=HEADERS, json=pay)
                    if r.status_code in [200, 201]:
                        enviar_telegram(f"Novo: {n}"); st.success("Salvo!"); st.cache_data.clear(); time.sleep(0.5); st.rerun()
            else:
                m = st.text_input("Médico")
                v = st.number_input("Valor R$", 0.0)
                dt = st.date_input("Data")
                if st.form_submit_button("CADASTRAR"):
                    pay = {"medico": m, "valor": float(v), "data_consulta": dt.strftime('%Y-%m-%d')}
                    r = requests.post(f"{URL_BASE}consultas", headers=HEADERS, json=pay)
                    if r.status_code in [200, 201]:
                        st.success("Salvo!"); st.cache_data.clear(); time.sleep(0.5); st.rerun()

elif menu == "Remover":
    if st.session_state.admin:
        tabela = st.selectbox("Remover de:", ["remedios", "consultas"])
        df_del = buscar_dados(tabela)
        if not df_del.empty:
            label = 'nome' if tabela == 'remedios' else 'medico'
            alvo = st.selectbox("Escolha o item:", df_del[label].tolist())
            if st.button("CONFIRMAR EXCLUSÃO"):
                id_alvo = df_del[df_del[label] == alvo]['id'].values[0]
                r = requests.delete(f"{URL_BASE}{tabela}?id=eq.{id_alvo}", headers=HEADERS)
                if r.status_code in [200, 204]:
                    st.warning("Removido!"); st.cache_data.clear(); time.sleep(0.5); st.rerun()
