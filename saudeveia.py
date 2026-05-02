import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURAÇÕES ---
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

# --- 2. CONFIGURAÇÃO DE TELA E CSS ---
st.set_page_config(page_title="Saúde Rock", layout="centered", initial_sidebar_state="collapsed")

# CSS para forçar colunas lado a lado no celular e reduzir espaços
st.markdown("""
    <style>
    [data-testid="column"] { width: 31% !important; flex: 1 1 31% !important; min-width: 31% !important; }
    .stMetric { padding: 0px !important; }
    div.block-container { padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

if "autenticado" not in st.session_state: st.session_state.autenticado = False
if "alertas_enviados" not in st.session_state: st.session_state.alertas_enviados = []

# Menu Lateral (Login)
with st.sidebar:
    st.title("🔒 ADM")
    if not st.session_state.autenticado:
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar") or senha == "1234":
            if senha == "1234": st.session_state.autenticado = True; st.rerun()
    else:
        if st.button("Sair"): st.session_state.autenticado = False; st.rerun()

# Menu Superior Compacto
st.markdown("<h3 style='text-align: center; margin-bottom: 0px;'>🏥 Minha Saúde</h3>", unsafe_allow_html=True)
aba = st.select_slider("", options=["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"], label_visibility="collapsed")

# --- 3. TELAS ---

if aba == "Estoque":
    df = buscar_dados("remedios")
    if not df.empty:
        hoje = datetime.now()
        for _, r in df.iterrows():
            ini = pd.to_datetime(r['data_inicio'])
            passados = (hoje - ini).days
            dose = float(r['dose_diaria'])
            atual = max(0.0, float(r['qtd_total']) - (passados * dose))
            resta = float(atual / dose) if dose > 0 else 0
            data_fim = hoje + timedelta(days=resta)
            
            # Alerta Telegram
            if 0 < resta <= 7 and r['id'] not in st.session_state.alertas_enviados:
                enviar_telegram(f"⚠️ {r['nome']} acaba em {int(resta)} dias!")
                st.session_state.alertas_enviados.append(r['id'])

            with st.container(border=True):
                st.markdown(f"**{r['nome'].upper()}**")
                c1, c2, c3 = st.columns(3) # Forçadas via CSS a ficarem lado a lado
                c1.metric("Qtd", f"{atual:g}")
                c2.metric("Dose", f"{dose:g}")
                c3.metric("Dias", int(resta))
                
                if resta > 0:
                    st.caption(f"📅 Término: {data_fim.strftime('%d/%m/%Y')}")
                else:
                    st.error("Estoque Zerado")

                if st.session_state.autenticado:
                    with st.expander("Ajustar Estoque"):
                        v_add = st.number_input("Qtd Comprada", 0.0, key=f"a_{r['id']}")
                        v_pago = st.number_input("Valor Pago R$", 0.0, key=f"p_{r['id']}")
                        if st.button("Salvar Registro", key=f"b_{r['id']}", use_container_width=True):
                            requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": float(atual+v_add), "data_inicio": hoje.strftime('%Y-%m-%d')})
                            requests.post(f"{URL_BASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(v_pago), "data_compra": hoje.strftime('%Y-%m-%d')})
                            st.cache_data.clear(); st.success("Ok!"); time.sleep(1); st.rerun()

elif aba == "Financeiro":
    st.subheader("💰 Gastos Mensais")
    df_com = buscar_dados("compras")
    df_con = buscar_dados("consultas")
    
    col_a, col_m = st.columns(2)
    ano_sel = col_a.selectbox("Ano", [2025, 2026], index=1)
    mes_sel = col_m.selectbox("Mês", list(range(1, 13)), index=datetime.now().month - 1)

    total_r = 0.0
    total_c = 0.0

    if not df_com.empty:
        df_com['data_compra'] = pd.to_datetime(df_com['data_compra'])
        filtro_r = df_com[(df_com['data_compra'].dt.year == ano_sel) & (df_com['data_compra'].dt.month == mes_sel)]
        total_r = filtro_r['valor'].sum()
        if not filtro_r.empty:
            st.write("**Detalhamento Remédios:**")
            st.dataframe(filtro_r[['nome_remedio', 'valor', 'data_compra']], hide_index=True)

    if not df_con.empty:
        df_con['data_consulta'] = pd.to_datetime(df_con['data_consulta'])
        filtro_c = df_con[(df_con['data_consulta'].dt.year == ano_sel) & (df_con['data_consulta'].dt.month == mes_sel)]
        total_c = filtro_c['valor'].sum()

    st.divider()
    st.metric("TOTAL INVESTIDO", f"R$ {total_r + total_c:,.2f}")
    st.info(f"Remédios: R$ {total_r:,.2f} | Consultas: R$ {total_c:,.2f}")

elif aba == "Consultas":
    df = buscar_dados("consultas")
    if not df.empty:
        st.dataframe(df[['data_consulta', 'medico', 'valor']], hide_index=True, use_container_width=True)

elif aba == "Cadastrar":
    if st.session_state.autenticado:
        tipo = st.segmented_control("Tipo", ["Remédio", "Consulta"], default="Remédio")
        with st.form("cad"):
            if tipo == "Remédio":
                n, q, d, p = st.text_input("Nome"), st.number_input("Qtd"), st.number_input("Dose/Dia"), st.number_input("Preço")
                if st.form_submit_button("Salvar", use_container_width=True):
                    requests.post(f"{URL_BASE}remedios", headers=HEADERS, json={"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "data_inicio": datetime.now().strftime('%Y-%m-%d')})
                    requests.post(f"{URL_BASE}compras", headers=HEADERS, json={"nome_remedio": n, "valor": float(p), "data_compra": datetime.now().strftime('%Y-%m-%d')})
                    st.cache_data.clear(); st.rerun()
            else:
                m, v = st.text_input("Médico"), st.number_input("Valor")
                if st.form_submit_button("Salvar", use_container_width=True):
                    requests.post(f"{URL_BASE}consultas", headers=HEADERS, json={"medico": m, "valor": float(v), "data_consulta": datetime.now().strftime('%Y-%m-%d')})
                    st.cache_data.clear(); st.rerun()
    else: st.warning("Acesse o menu ADM na lateral.")

elif aba == "Remover":
    if st.session_state.autenticado:
        tab = st.selectbox("Tabela", ["remedios", "consultas", "compras"])
        df_del = buscar_dados(tab)
        if not df_del.empty:
            c = 'nome' if tab == 'remedios' else ('nome_remedio' if tab == 'compras' else 'medico')
            item = st.selectbox("Item", df_del[c].tolist())
            if st.button("🗑️ APAGAR", type="primary", use_container_width=True):
                id_i = df_del[df_del[c] == item]['id'].values[0]
                requests.delete(f"{URL_BASE}{tab}?id=eq.{id_i}", headers=HEADERS)
                if tab == "remedios": requests.delete(f"{URL_BASE}compras?nome_remedio=eq.{item}", headers=HEADERS)
                st.cache_data.clear(); st.rerun()
