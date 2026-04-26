import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURAÇÕES (SUPABASE E TELEGRAM) ---
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
        res = requests.get(f"{URL_BASE}{tabela}?select=*", headers=HEADERS, timeout=10)
        return pd.DataFrame(res.json()) if res.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

# --- 2. INTERFACE E SEGURANÇA ---
st.set_page_config(page_title="Gestão de Saúde Rock", layout="centered")
if "autenticado" not in st.session_state: st.session_state.autenticado = False

with st.sidebar:
    st.title("⚙️ Painel")
    if not st.session_state.autenticado:
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar") or senha == "1234":
            if senha == "1234": st.session_state.autenticado = True; st.rerun()
    else:
        if st.button("Sair"): st.session_state.autenticado = False; st.rerun()
    
    st.divider()
    aba = st.radio("Menu", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"])

# --- 3. FUNCIONALIDADES ---

if aba == "Estoque":
    st.subheader("📋 Status Detalhado")
    df = buscar_dados("remedios")
    if not df.empty:
        hoje = datetime.now()
        for _, r in df.iterrows():
            # PILAR: Cálculo com doses fracionadas
            ini = pd.to_datetime(r['data_inicio'])
            dias_passados = (hoje - ini).days
            dose = float(r['dose_diaria'])
            estoque_atual = max(0.0, float(r['qtd_total']) - (dias_passados * dose))
            resta_dias = float(estoque_atual / dose) if dose > 0 else 0
            data_fim = hoje + timedelta(days=resta_dias)
            
            with st.container(border=True):
                st.markdown(f"### 💊 {r['nome'].upper()}")
                c1, c2, c3 = st.columns(3)
                
                # RECOLOCANDO AS INFORMAÇÕES QUE VOCÊ PEDIU
                c1.metric("Estoque Atual", f"{estoque_atual:g}")
                c2.metric("Dose Diária", f"{dose:g}")
                c3.metric("Dias Restantes", int(resta_dias))
                
                st.info(f"📅 Previsão de Término: **{data_fim.strftime('%d/%m/%Y')}**")
                
                if st.session_state.autenticado:
                    with st.expander("➕ Ajustar Estoque / Registrar Compra"):
                        v_add = st.number_input("Qtd Adquirida", 0.0, key=f"add_{r['id']}")
                        v_pago = st.number_input("Valor Pago nesta Compra (R$)", 0.0, key=f"v_{r['id']}")
                        if st.button("Salvar Ajuste", key=f"btn_{r['id']}", use_container_width=True):
                            # Atualiza estoque e reseta data
                            requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, 
                                           json={"qtd_total": float(estoque_atual + v_add), "data_inicio": hoje.strftime('%Y-%m-%d')})
                            # Registra novo gasto no financeiro
                            requests.post(f"{URL_BASE}compras", headers=HEADERS, 
                                           json={"nome_remedio": r['nome'], "valor": float(v_pago), "data_compra": hoje.strftime('%Y-%m-%d')})
                            
                            enviar_telegram(f"✅ Ajuste: {r['nome']} (+{v_add} un) | Gasto: R$ {v_pago:.2f}")
                            st.success("Estoque e Financeiro atualizados!")
                            st.cache_data.clear(); time.sleep(1.5); st.rerun()

elif aba == "Financeiro":
    st.subheader("💰 Resumo de Investimento")
    df_com = buscar_dados("compras")
    df_con = buscar_dados("consultas")
    
    # PILAR: Soma dinâmica de todos os gastos registrados
    total_r = df_com['valor'].sum() if not df_com.empty else 0
    total_c = df_con['valor'].sum() if not df_con.empty else 0
    
    col1, col2 = st.columns(2)
    col1.metric("Total em Remédios", f"R$ {total_r:,.2f}")
    col2.metric("Total em Consultas", f"R$ {total_c:,.2f}")
    
    st.divider()
    st.markdown(f"## TOTAL GERAL: R$ {total_r + total_c:,.2f}")

elif aba == "Consultas":
    st.subheader("🩺 Histórico Médico")
    df = buscar_dados("consultas")
    if not df.empty:
        st.dataframe(df[['data_consulta', 'medico', 'valor']], hide_index=True, use_container_width=True)

elif aba == "Cadastrar":
    if st.session_state.autenticado:
        opcao = st.selectbox("O que deseja cadastrar?", ["Remédio", "Consulta"])
        with st.form("f_cad"):
            if opcao == "Remédio":
                n, q, d, p = st.text_input("Nome"), st.number_input("Quantidade Total"), st.number_input("Dose Diária"), st.number_input("Preço de Compra (R$)")
                if st.form_submit_button("SALVAR"):
                    requests.post(f"{URL_BASE}remedios", headers=HEADERS, json={"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "data_inicio": datetime.now().strftime('%Y-%m-%d')})
                    requests.post(f"{URL_BASE}compras", headers=HEADERS, json={"nome_remedio": n, "valor": float(p), "data_compra": datetime.now().strftime('%Y-%m-%d')})
                    enviar_telegram(f"🆕 Novo Remédio: {n} (Dose {d})")
                    st.success("Salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()
            else:
                m, v = st.text_input("Médico"), st.number_input("Valor")
                if st.form_submit_button("SALVAR"):
                    requests.post(f"{URL_BASE}consultas", headers=HEADERS, json={"medico": m, "valor": float(v), "data_consulta": datetime.now().strftime('%Y-%m-%d')})
                    st.success("Salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()

elif aba == "Remover":
    if st.session_state.autenticado:
        tab = st.selectbox("Onde remover?", ["remedios", "consultas", "compras"])
        df_del = buscar_dados(tab)
        if not df_del.empty:
            c = 'nome' if tab == 'remedios' else ('nome_remedio' if tab == 'compras' else 'medico')
            it = st.selectbox("Selecione:", df_del[c].tolist())
            if st.button("🗑️ EXCLUIR"):
                id_i = df_del[df_del[c] == it]['id'].values[0]
                requests.delete(f"{URL_BASE}{tab}?id=eq.{id_i}", headers=HEADERS)
                st.cache_data.clear(); time.sleep(1); st.rerun()
