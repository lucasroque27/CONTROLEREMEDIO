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
    st.subheader("📋 Status Detalhado do Estoque")
    df = buscar_dados("remedios")
    if df.empty:
        st.info("Nenhum dado encontrado.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            # PILAR: Cálculo preciso de doses e datas
            data_ini = pd.to_datetime(r['data_inicio'])
            dias_corridos = (hoje - data_ini).days
            qtd_consumida = dias_corridos * float(r['dose_diaria'])
            qtd_atual = max(0.0, float(r['qtd_total']) - qtd_consumida)
            
            dias_restantes = float(qtd_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)
            
            with st.container(border=True):
                st.markdown(f"### 💊 {r['nome'].upper()}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Estoque Atual", f"{qtd_atual:g}")
                c2.metric("Dose Diária", f"{r['dose_diaria']:g}")
                c3.metric("Dias Restantes", int(dias_restantes))
                
                st.write(f"📅 Previsão de Término: **{data_fim.strftime('%Y-%m-%d')}**")
                
                if st.session_state.autenticado:
                    with st.expander("⚙️ Ajustar Estoque / Preço"):
                        v_add = st.number_input("Adicionar Qtd (unidades)", 0.0, key=f"a_{r['id']}")
                        v_prc = st.number_input("Preço Atual (R$)", 0.0, value=float(r['preco']), key=f"p_{r['id']}")
                        if st.button("Confirmar Alteração", key=f"b_{r['id']}", use_container_width=True):
                            # Reset do pilar: Atualiza estoque total e reinicia contagem de dias
                            pay = {"qtd_total": float(qtd_atual + v_add), "data_inicio": hoje.strftime('%Y-%m-%d'), "preco": float(v_prc)}
                            res = requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, json=pay)
                            if res.status_code in [200, 204]:
                                enviar_telegram(f"✅ Estoque atualizado: {r['nome']} (+{v_add} un). Novo estoque total: {qtd_atual + v_add:g}")
                                st.cache_data.clear(); time.sleep(0.5); st.rerun()

elif aba == "Financeiro":
    st.subheader("💰 Controle de Gastos")
    df_r = buscar_dados("remedios")
    df_c = buscar_dados("consultas")
    
    tot_r = df_r['preco'].sum() if not df_r.empty else 0
    tot_c = df_c['valor'].sum() if not df_c.empty else 0
    
    c1, c2 = st.columns(2)
    c1.metric("Gasto com Remédios", f"R$ {tot_r:,.2f}")
    c2.metric("Gasto com Consultas", f"R$ {tot_c:,.2f}")
    
    st.divider()
    st.markdown(f"## **INVESTIMENTO TOTAL: R$ {tot_r + tot_c:,.2f}**")

elif aba == "Consultas":
    st.subheader("🩺 Histórico Médico")
    df = buscar_dados("consultas")
    if not df.empty:
        st.dataframe(df[['data_consulta', 'medico', 'valor']], use_container_width=True, hide_index=True)

elif aba == "Cadastrar":
    if not st.session_state.autenticado:
        st.warning("Acesse com a senha na barra lateral para cadastrar.")
    else:
        tipo = st.selectbox("Escolha o tipo:", ["Remédio", "Consulta"])
        with st.form("form_novo"):
            if tipo == "Remédio":
                n = st.text_input("Nome")
                q = st.number_input("Quantidade Total em Mãos", 0.0)
                d = st.number_input("Dose Diária (Ex: 1.5)", 0.0)
                p = st.number_input("Preço Pago (R$)", 0.0)
                if st.form_submit_button("SALVAR MEDICAMENTO"):
                    pay = {"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "preco": float(p), "data_inicio": datetime.now().strftime('%Y-%m-%d')}
                    r = requests.post(f"{URL_BASE}remedios", headers=HEADERS, json=pay)
                    if r.status_code in [200, 201]:
                        enviar_telegram(f"🆕 Novo Remédio: {n} | Dose: {d} | Qtd: {q}")
                        st.cache_data.clear(); time.sleep(0.5); st.rerun()
            else:
                m = st.text_input("Médico / Especialidade")
                v = st.number_input("Valor da Consulta (R$)", 0.0)
                if st.form_submit_button("SALVAR CONSULTA"):
                    pay = {"medico": m, "valor": float(v), "data_consulta": datetime.now().strftime('%Y-%m-%d')}
                    requests.post(f"{URL_BASE}consultas", headers=HEADERS, json=pay)
                    st.cache_data.clear(); time.sleep(0.5); st.rerun()

elif aba == "Remover":
    if not st.session_state.autenticado:
        st.warning("Acesse com a senha para excluir dados.")
    else:
        tabela = st.selectbox("Apagar de:", ["remedios", "consultas"])
        df_del = buscar_dados(tabela)
        if not df_del.empty:
            campo = "nome" if tabela == "remedios" else "medico"
            item = st.selectbox("Selecione o item:", df_del[campo].tolist())
            if st.button("🗑️ EXCLUIR ITEM DEFINITIVAMENTE", type="primary"):
                id_item = df_del[df_del[campo] == item]['id'].values[0]
                requests.delete(f"{URL_BASE}{tabela}?id=eq.{id_item}", headers=HEADERS)
                st.cache_data.clear(); time.sleep(0.5); st.rerun()
