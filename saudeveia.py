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

def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem}, timeout=5)
    except: pass

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

# --- 2. INICIALIZAÇÃO E ALERTA DE ENTRADA ÚNICO ---
st.set_page_config(page_title="Saúde Rock", page_icon="💊", layout="wide")

# TRAVA 1: Só avisa que alguém entrou UMA VEZ por sessão
if "notificou_entrada" not in st.session_state:
    enviar_telegram("🔌 App Acessado: Alguém entrou no sistema de saúde.")
    st.session_state.notificou_entrada = True

# --- 3. MENU ---
with st.sidebar:
    st.title("🏥 Gestão")
    if "admin" not in st.session_state: st.session_state.admin = False
    if not st.session_state.admin:
        pw = st.text_input("Senha", type="password")
        if st.button("Acessar"):
            if pw == "1234": st.session_state.admin = True; st.rerun()
    else:
        if st.button("Sair"): st.session_state.admin = False; st.rerun()
    aba = st.radio("Navegação", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"])

meses_pt = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}

# --- 4. ESTOQUE COM ALERTA INTELIGENTE ---
if aba == "Estoque":
    st.subheader("📋 Resumo de Medicamentos")
    df = api_get("remedios")
    
    if not df.empty:
        hoje = datetime.now()
        itens_criticos = []

        for _, r in df.iterrows():
            dias_p = (hoje - r['data_inicio']).days
            estoque = max(0, int(r['qtd_total'] - (dias_p * r['dose_diaria'])))
            dias_r = int(estoque / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_f = hoje + timedelta(days=dias_r)
            
            # Identifica se está no nível de alerta (menos de 7 dias)
            if dias_r < 7:
                itens_criticos.append(f"- {r['nome'].upper()} ({dias_r} dias rest.)")

            with st.container(border=True):
                c_tit, c_stat = st.columns([2, 1])
                c_tit.markdown(f"**{r['nome'].upper()}**")
                if dias_r < 7: c_stat.error("🚨 REPOR")
                elif dias_r < 15: c_stat.warning("⚠️ ALERTA")
                else: c_stat.success("✅ OK")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Qtd", f"{estoque} un.")
                m2.metric("Dose", f"{r['dose_diaria']}")
                m3.metric("Restam", f"{dias_r} d")
                m4.metric("Fim", f"{data_f.day}/{meses_pt[data_f.month]}")

                if st.session_state.admin:
                    with st.expander("Reposição"):
                        nq = st.number_input("Qtd comprada", 1, 500, 30, key=f"q_{r['id']}")
                        np = st.number_input("Preço R$", 0.0, 5000.0, float(r['preco']), key=f"p_{r['id']}")
                        if st.button("Salvar Estoque", key=f"b_{r['id']}"):
                            requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={
                                "qtd_total": int(estoque + nq), "data_inicio": str(hoje.date()), "preco": float(np)
                            })
                            requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":r['nome'], "valor":float(np), "data_compra":str(hoje.date())})
                            # Alerta de reposição (Sempre enviado pois é uma ação manual sua)
                            enviar_telegram(f"✅ Reposição: {r['nome']} atualizado para {int(estoque + nq)} unidades.")
                            st.rerun()

        # TRAVA 2: Envia a lista de alertas apenas UMA VEZ por acesso ao app
        if itens_criticos and "notificou_estoque" not in st.session_state:
            msg_critica = "⚠️ **ESTOQUE BAIXO!**\n" + "\n".join(itens_criticos)
            enviar_telegram(msg_critica)
            st.session_state.notificou_estoque = True

# --- (Demais abas permanecem funcionais e completas abaixo) ---
elif aba == "Financeiro":
    st.subheader("💰 Resumo Financeiro")
    df_f = api_get("compras")
    if not df_f.empty:
        st.metric("Total Gasto", f"R$ {df_f['valor'].sum():.2f}")
        st.dataframe(df_f[['data_compra', 'nome_remedio', 'valor']], use_container_width=True)

elif aba == "Consultas":
    st.subheader("🩺 Consultas")
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            with st.container(border=True):
                st.write(f"**{c['medico']}** | R$ {c['valor']:.2f} | {c['data_consulta'].strftime('%d/%m/%Y')}")

elif aba == "Cadastrar":
    st.subheader("➕ Novo")
    if st.session_state.admin:
        with st.form("c"):
            n = st.text_input("Nome")
            c1, c2, c3 = st.columns(3)
            q = c1.number_input("Qtd", 1)
            d = c2.number_input("Dose", 0.1, 10.0, 1.0)
            p = c3.number_input("Preço", 0.0)
            if st.form_submit_button("Cadastrar"):
                requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":n,"valor":float(p),"data_compra":str(datetime.now().date())})
                enviar_telegram(f"🆕 Novo remédio cadastrado: {n}")
                st.rerun()

elif aba == "Remover":
    st.subheader("🗑️ Remover")
    if st.session_state.admin:
        df_d = api_get("remedios")
        if not df_d.empty:
            it = st.selectbox("Escolha o item", df_d['nome'].tolist())
            if st.button("Excluir"):
                id_d = df_d[df_d['nome'] == it]['id'].values[0]
                requests.delete(f"{URL_SUPABASE}remedios?id=eq.{id_d}", headers=HEADERS)
                st.rerun()
