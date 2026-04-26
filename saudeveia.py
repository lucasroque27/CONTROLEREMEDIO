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

# --- INTERFACE ---
st.set_page_config(page_title="Controle Saúde Rock", layout="centered")
if "adm" not in st.session_state: st.session_state.adm = False

with st.sidebar:
    st.title("💊 Navegação")
    if not st.session_state.adm:
        pw = st.text_input("Senha", type="password")
        if st.button("Acessar") or pw == "1234":
            if pw == "1234": st.session_state.adm = True; st.rerun()
    else:
        if st.button("Sair"): st.session_state.adm = False; st.rerun()
    aba = st.radio("Menu:", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"])

# --- TELAS ---

if aba == "Estoque":
    st.subheader("📋 Status do Estoque")
    df = buscar_dados("remedios")
    if not df.empty:
        hoje = datetime.now()
        for _, r in df.iterrows():
            ini = pd.to_datetime(r['data_inicio'])
            passados = (hoje - ini).days
            dose = float(r['dose_diaria'])
            # Pilar: Cálculo de dose fracionada
            atual = max(0.0, float(r['qtd_total']) - (passados * dose))
            resta = float(atual / dose) if dose > 0 else 0
            
            with st.container(border=True):
                st.markdown(f"### {r['nome'].upper()}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Estoque", f"{atual:g}")
                c2.metric("Dose/Dia", f"{dose:g}")
                c3.metric("Dias", int(resta))
                
                if st.session_state.adm:
                    with st.expander("Ajustar Estoque (Nova Compra)"):
                        v_add = st.number_input("Qtd Comprada", 0.0, key=f"add_{r['id']}")
                        v_pago = st.number_input("Valor Pago (R$)", 0.0, key=f"v_{r['id']}")
                        if st.button("Confirmar Ajuste", key=f"btn_{r['id']}", use_container_width=True):
                            # 1. Atualiza estoque no banco
                            pay_rem = {"qtd_total": float(atual + v_add), "data_inicio": hoje.strftime('%Y-%m-%d')}
                            res_rem = requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, json=pay_rem)
                            
                            # 2. REGISTRA O GASTO NA TABELA DE COMPRAS (O segredo do financeiro)
                            pay_com = {"nome_remedio": r['nome'], "valor": float(v_pago), "data_compra": hoje.strftime('%Y-%m-%d')}
                            res_com = requests.post(f"{URL_BASE}compras", headers=HEADERS, json=pay_com)
                            
                            if res_rem.status_code in [200, 204] and res_com.status_code in [200, 201]:
                                enviar_telegram(f"✅ Compra: {r['nome']} (+{v_add} un) - R$ {v_pago:.2f}")
                                st.success("Ajuste e Gasto salvos com sucesso!")
                                st.cache_data.clear(); time.sleep(2); st.rerun()
                            else:
                                st.error("Erro ao salvar no banco. Verifique o SQL da tabela 'compras'.")

elif aba == "Financeiro":
    st.subheader("💰 Resumo Financeiro Real")
    # Aqui o sistema soma TODAS as compras já feitas
    df_compras = buscar_dados("compras")
    df_consultas = buscar_dados("consultas")
    
    total_remedios = df_compras['valor'].sum() if not df_compras.empty else 0
    total_consultas = df_consultas['valor'].sum() if not df_consultas.empty else 0
    
    col1, col2 = st.columns(2)
    col1.metric("Total em Medicamentos", f"R$ {total_remedios:,.2f}")
    col2.metric("Total em Consultas", f"R$ {total_consultas:,.2f}")
    
    st.divider()
    st.metric("INVESTIMENTO TOTAL", f"R$ {total_remedios + total_consultas:,.2f}")
    
    if not df_compras.empty:
        with st.expander("Ver Histórico de Compras"):
            st.dataframe(df_compras[['data_compra', 'nome_remedio', 'valor']], hide_index=True)

elif aba == "Consultas":
    st.subheader("🩺 Histórico de Consultas")
    df = buscar_dados("consultas")
    if not df.empty:
        st.dataframe(df[['data_consulta', 'medico', 'valor']], hide_index=True, use_container_width=True)

elif aba == "Cadastrar":
    if st.session_state.adm:
        tipo = st.selectbox("Tipo:", ["Remédio", "Consulta"])
        with st.form("cad"):
            if tipo == "Remédio":
                n, q, d, p = st.text_input("Nome"), st.number_input("Qtd"), st.number_input("Dose/Dia"), st.number_input("Preço Inicial (R$)")
                if st.form_submit_button("SALVAR"):
                    # Salva o remédio
                    requests.post(f"{URL_BASE}remedios", headers=HEADERS, json={"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "data_inicio": datetime.now().strftime('%Y-%m-%d')})
                    # Registra o primeiro gasto
                    requests.post(f"{URL_BASE}compras", headers=HEADERS, json={"nome_remedio": n, "valor": float(p), "data_compra": datetime.now().strftime('%Y-%m-%d')})
                    st.success("Cadastrado com sucesso!"); st.cache_data.clear(); time.sleep(1); st.rerun()
            else:
                m, v = st.text_input("Médico"), st.number_input("Valor")
                if st.form_submit_button("SALVAR"):
                    requests.post(f"{URL_BASE}consultas", headers=HEADERS, json={"medico": m, "valor": float(v), "data_consulta": datetime.now().strftime('%Y-%m-%d')})
                    st.success("Consulta Salva!"); st.cache_data.clear(); time.sleep(1); st.rerun()

elif aba == "Remover":
    if st.session_state.adm:
        tab = st.selectbox("Tabela:", ["remedios", "consultas", "compras"])
        df_del = buscar_dados(tab)
        if not df_del.empty:
            campo = 'nome' if tab == 'remedios' else ('nome_remedio' if tab == 'compras' else 'medico')
            item = st.selectbox("Item:", df_del[campo].tolist())
            if st.button("🗑️ EXCLUIR"):
                id_i = df_del[df_del[campo] == item]['id'].values[0]
                requests.delete(f"{URL_BASE}{tab}?id=eq.{id_i}", headers=HEADERS)
                st.warning("Excluído!"); st.cache_data.clear(); time.sleep(1); st.rerun()
