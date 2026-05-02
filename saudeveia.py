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

# --- 2. INTERFACE APP (FOCO EM CELULAR) ---
st.set_page_config(page_title="Saúde Rock", layout="centered", initial_sidebar_state="collapsed")

if "autenticado" not in st.session_state: st.session_state.autenticado = False
if "alertas_enviados" not in st.session_state: st.session_state.alertas_enviados = []

# Menu Lateral apenas para Login
with st.sidebar:
    st.title("🔒 Login ADM")
    if not st.session_state.autenticado:
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True) or senha == "1234":
            if senha == "1234": st.session_state.autenticado = True; st.rerun()
    else:
        st.success("Modo Editor Ativo")
        if st.button("Sair", use_container_width=True):
            st.session_state.autenticado = False; st.rerun()

# Botões de Navegação no Topo (Estilo App)
st.markdown("<h3 style='text-align: center;'>📱 Minha Saúde</h3>", unsafe_allow_html=True)
aba = st.radio("Menu", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"], 
               horizontal=True, label_visibility="collapsed")
st.divider()

# --- 3. FUNCIONALIDADES ---

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
            
            # Alerta Inteligente (Apenas 7 dias ou fim)
            if 0 < resta <= 7 and r['id'] not in st.session_state.alertas_enviados:
                enviar_telegram(f"⚠️ {r['nome']} acaba em {int(resta)} dias!")
                st.session_state.alertas_enviados.append(r['id'])
            
            with st.container(border=True):
                st.markdown(f"**{r['nome'].upper()}**")
                c1, c2, c3 = st.columns(3)
                c1.metric("Qtd", f"{atual:g}")
                c2.metric("Dose", f"{dose:g}")
                c3.metric("Dias", int(resta))
                
                if resta > 0:
                    st.caption(f"📅 Acaba em: {data_fim.strftime('%d/%m/%Y')}")
                else:
                    st.error("Acabou!")

                if st.session_state.autenticado:
                    with st.expander("Ajustar"):
                        v_add = st.number_input("Adicionar Qtd", 0.0, key=f"a_{r['id']}")
                        v_pago = st.number_input("Preço R$", 0.0, key=f"p_{r['id']}")
                        if st.button("Salvar", key=f"b_{r['id']}", use_container_width=True):
                            requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, 
                                           json={"qtd_total": float(atual+v_add), "data_inicio": hoje.strftime('%Y-%m-%d')})
                            requests.post(f"{URL_BASE}compras", headers=HEADERS, 
                                           json={"nome_remedio": r['nome'], "valor": float(v_pago), "data_compra": hoje.strftime('%Y-%m-%d')})
                            st.cache_data.clear(); st.rerun()

elif aba == "Financeiro":
    df_com = buscar_dados("compras")
    df_con = buscar_dados("consultas")
    if not df_com.empty or not df_con.empty:
        c1, c2 = st.columns(2)
        ano = c1.selectbox("Ano", [2025, 2026])
        mes = c2.selectbox("Mês", list(range(1,13)), index=datetime.now().month-1)
        
        # Filtros
        if not df_com.empty: 
            df_com['d'] = pd.to_datetime(df_com['data_compra'])
            f_com = df_com[(df_com['d'].dt.year == ano) & (df_com['d'].dt.month == mes)]
            gast_r = f_com['valor'].sum()
        else: gast_r = 0
            
        if not df_con.empty:
            df_con['d'] = pd.to_datetime(df_con['data_consulta'])
            f_con = df_con[(df_con['d'].dt.year == ano) & (df_con['d'].dt.month == mes)]
            gast_c = f_con['valor'].sum()
        else: gast_c = 0

        st.metric("Total no Mês", f"R$ {gast_r + gast_c:,.2f}")
        st.write(f"Remédios: R$ {gast_r:,.2f} | Consultas: R$ {gast_c:,.2f}")
        
        if st.button("📥 Exportar Planilha (CSV)", use_container_width=True):
            rel = pd.concat([df_com, df_con], sort=False)
            csv = rel.to_csv(index=False).encode('utf-8')
            st.download_button("Baixar Arquivo", csv, "relatorio.csv", "text/csv", use_container_width=True)

elif aba == "Consultas":
    df = buscar_dados("consultas")
    if not df.empty: st.table(df[['data_consulta', 'medico', 'valor']])

elif aba == "Cadastrar":
    if st.session_state.autenticado:
        tipo = st.radio("O que cadastrar?", ["Remédio", "Consulta"], horizontal=True)
        with st.form("cad"):
            if tipo == "Remédio":
                n = st.text_input("Nome")
                q = st.number_input("Qtd")
                d = st.number_input("Dose/Dia")
                p = st.number_input("Preço")
                if st.form_submit_button("Salvar", use_container_width=True):
                    requests.post(f"{URL_BASE}remedios", headers=HEADERS, json={"nome":n, "qtd_total":float(q), "dose_diaria":float(d), "data_inicio":datetime.now().strftime('%Y-%m-%d')})
                    requests.post(f"{URL_BASE}compras", headers=HEADERS, json={"nome_remedio":n, "valor":float(p), "data_compra":datetime.now().strftime('%Y-%m-%d')})
                    st.cache_data.clear(); st.rerun()
            else:
                m = st.text_input("Médico")
                v = st.number_input("Valor")
                if st.form_submit_button("Salvar", use_container_width=True):
                    requests.post(f"{URL_BASE}consultas", headers=HEADERS, json={"medico":m, "valor":float(v), "data_consulta":datetime.now().strftime('%Y-%m-%d')})
                    st.cache_data.clear(); st.rerun()
    else: st.info("Faça login na barra lateral.")

elif aba == "Remover":
    if st.session_state.autenticado:
        tab = st.selectbox("Tabela", ["remedios", "consultas", "compras"])
        df_del = buscar_dados(tab)
        if not df_del.empty:
            col = 'nome' if tab=='remedios' else ('nome_remedio' if tab=='compras' else 'medico')
            item = st.selectbox("Item", df_del[col].tolist())
            if st.button("🗑️ APAGAR TUDO", type="primary", use_container_width=True):
                id_i = df_del[df_del[col] == item]['id'].values[0]
                if tab == "remedios":
                    requests.delete(f"{URL_BASE}remedios?id=eq.{id_i}", headers=HEADERS)
                    requests.delete(f"{URL_BASE}compras?nome_remedio=eq.{item}", headers=HEADERS)
                else:
                    requests.delete(f"{URL_BASE}{tab}?id=eq.{id_i}", headers=HEADERS)
                st.cache_data.clear(); st.rerun()
    else: st.info("Faça login na barra lateral.")
