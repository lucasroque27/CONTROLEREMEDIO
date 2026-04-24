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

HEADERS = {
    "apikey": API_KEY, 
    "Authorization": f"Bearer {API_KEY}", 
    "Content-Type": "application/json", 
    "Prefer": "return=representation"
}

# Funções de Suporte
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

# --- 2. INTERFACE E ESTILO (VISUAL ORIGINAL AJUSTADO) ---
st.set_page_config(page_title="Saúde Rock", page_icon="💊", layout="wide")

st.markdown("""
    <style>
    .block-container { padding: 1rem; }
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    .stAlert { padding: 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

# Alerta de Entrada (Apenas uma vez)
if "entrada_notificada" not in st.session_state:
    enviar_telegram("⚠️ App Saúde acessado.")
    st.session_state.entrada_notificada = True

# --- 3. MENU LATERAL ---
with st.sidebar:
    st.title("🏥 Gestão")
    if "admin" not in st.session_state: st.session_state.admin = False
    
    if not st.session_state.admin:
        pw = st.text_input("Senha ADM", type="password")
        if st.button("Acessar"):
            if pw == "1234": st.session_state.admin = True; st.rerun()
    else:
        if st.button("Sair"): st.session_state.admin = False; st.rerun()

    aba = st.radio("Navegação", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"])

meses_pt = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}

# --- 4. TELA DE ESTOQUE ---
if aba == "Estoque":
    st.subheader("📋 Resumo de Medicamentos")
    df = api_get("remedios")
    
    if df.empty:
        st.info("Nenhum dado encontrado.")
    else:
        hoje = datetime.now()
        alertas_lista = []

        for _, r in df.iterrows():
            # Cálculos de Estoque
            dias_passados = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_passados * r['dose_diaria'])))
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)
            
            # Verificar nível crítico para o Telegram
            if dias_restantes < 7:
                alertas_lista.append(f"🚨 {r['nome'].upper()} ({dias_restantes} dias)")

            # Visual de Card (Igual ao primeiro que você viu)
            with st.container(border=True):
                col_nome, col_status = st.columns([2, 1])
                col_nome.markdown(f"**{r['nome'].upper()}**")
                
                if dias_restantes < 7: col_status.error("REPOR", icon="🚨")
                elif dias_restantes < 15: col_status.warning("ALERTA", icon="⚠️")
                else: col_status.success("OK", icon="✅")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Qtd", f"{estoque_atual} un.")
                m2.metric("Dose", f"{r['dose_diaria']}")
                m3.metric("Restam", f"{dias_restantes}d")
                m4.metric("Acaba", f"{data_fim.day}/{meses_pt[data_fim.month]}")

                # Opção de Reposição para Admin
                if st.session_state.admin:
                    with st.expander("Ajustar Medicamento"):
                        c1, c2 = st.columns(2)
                        nova_qtd = c1.number_input("Qtd comprada", 1, 500, 30, key=f"q_{r['id']}")
                        novo_preco = c2.number_input("Preço R$", 0.0, 5000.0, float(r['preco']), key=f"p_{r['id']}")
                        
                        if st.button("Confirmar Reposição", key=f"b_{r['id']}"):
                            # Atualiza Banco
                            requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={
                                "qtd_total": int(estoque_atual + nova_qtd), 
                                "data_inicio": str(hoje.date()), 
                                "preco": float(novo_preco)
                            })
                            requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={
                                "nome_remedio": r['nome'], 
                                "valor": float(novo_preco), 
                                "data_compra": str(hoje.date())
                            })
                            
                            # Alerta de Reposição
                            enviar_telegram(f"✅ Reposição realizada!\n💊 {r['nome']}\n📦 Novo total: {int(estoque_atual + nova_qtd)} un.")
                            st.success("Atualizado!"); time.sleep(1); st.rerun()

        # Notificação Inteligente de Estoque Baixo
        if alertas_lista and "estoque_notificado" not in st.session_state:
            enviar_telegram("⚠️ ATENÇÃO: Itens quase acabando!\n" + "\n".join(alertas_lista))
            st.session_state.estoque_notificado = True

# --- 5. OUTRAS TELAS ---
elif aba == "Financeiro":
    st.subheader("💰 Gastos")
    df_f = api_get("compras")
    if not df_f.empty:
        st.metric("Total Acumulado", f"R$ {df_f['valor'].sum():.2f}")
        st.dataframe(df_f[['data_compra', 'nome_remedio', 'valor']], use_container_width=True)

elif aba == "Consultas":
    st.subheader("🩺 Consultas")
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            with st.container(border=True):
                st.write(f"**{c['medico']}** | R$ {c['valor']:.2f} | {c['data_consulta'].strftime('%d/%m/%Y')}")

elif aba == "Cadastrar":
    st.subheader("➕ Novo Cadastro")
    if st.session_state.admin:
        with st.form("cad"):
            nome = st.text_input("Nome")
            c1, c2, c3 = st.columns(3)
            qtd = c1.number_input("Qtd Inicial", 1)
            dose = c2.number_input("Dose", 0.1, 10.0, 1.0)
            preco = c3.number_input("Preço", 0.0)
            if st.form_submit_button("Salvar"):
                requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":nome,"qtd_total":int(qtd),"dose_diaria":float(dose),"preco":float(preco),"data_inicio":str(datetime.now().date())})
                requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":nome,"valor":float(preco),"data_compra":str(datetime.now().date())})
                enviar_telegram(f"🆕 Novo cadastro: {nome}")
                st.rerun()
    else: st.warning("Faça login como ADM.")

elif aba == "Remover":
    st.subheader("🗑️ Remover Item")
    if st.session_state.admin:
        df_d = api_get("remedios")
        if not df_d.empty:
            it = st.selectbox("Escolha o item", df_d['nome'].tolist())
            if st.button("Confirmar Exclusão"):
                id_item = df_d[df_d['nome'] == it]['id'].values[0]
                requests.delete(f"{URL_SUPABASE}remedios?id=eq.{id_item}", headers=HEADERS)
                st.rerun()
