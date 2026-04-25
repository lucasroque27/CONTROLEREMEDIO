import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import time

# --- 1. CONFIGURAÇÕES E CONEXÃO (CORRIGIDO) ---
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
                      json={"chat_id": "5256921022", "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

@st.cache_data(ttl=1)
def buscar_dados(tabela):
    try:
        res = requests.get(f"{URL_BASE}{tabela}?select=*&order=id.desc", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            for col in ['data_inicio', 'data_consulta', 'data_compra']:
                if not df.empty and col in df.columns: 
                    df[col] = pd.to_datetime(df[col])
            return df
    except: pass
    return pd.DataFrame()

# --- 2. INTERFACE PROFISSIONAL ---
st.set_page_config(page_title="Gestão de Saúde", layout="centered")
st.markdown("""
    <style>
    .card { background: white; border-radius: 10px; padding: 18px; margin-bottom: 12px; border: 1px solid #eee; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); }
    .label { color: #666; font-size: 0.85rem; margin-bottom: 2px; }
    .value { font-size: 1.2rem; font-weight: bold; color: #2c3e50; margin-top: -5px; }
    </style>
""", unsafe_allow_html=True)

if "admin" not in st.session_state: st.session_state.admin = False

with st.sidebar:
    st.title("💊 Gestão Saúde")
    if not st.session_state.admin:
        pw = st.text_input("Senha ADM", type="password", key="login_p")
        if st.button("Acessar", use_container_width=True) or (pw == "1234"):
            if pw == "1234":
                st.session_state.admin = True
                st.rerun()
    else:
        if st.button("Sair do Modo ADM", use_container_width=True): 
            st.session_state.admin = False
            st.rerun()
    aba = st.radio("Menu:", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"], key="nav_main")

# --- 3. TELAS ---

if aba == "Estoque":
    st.subheader("📋 Resumo de Medicamentos")
    df = buscar_dados("remedios")
    if not df.empty:
        hoje = datetime.now()
        for _, r in df.iterrows():
            d_passados = (hoje - r['data_inicio']).days
            est_at = max(0.0, float(r['qtd_total']) - (d_passados * float(r['dose_diaria'])))
            d_restantes = float(est_at / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_f = hoje + timedelta(days=d_restantes)
            
            st.markdown(f"""
            <div class="card">
                <div style="font-weight:bold; color:#34495e; font-size:1.1rem;">💊 {r['nome'].upper()}</div>
                <hr style="margin: 10px 0; border:0; border-top:1px solid #f5f5f5;">
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div><p class="label">Qtd</p><p class="value">{est_at:g}</p></div>
                    <div><p class="label">Dose/Dia</p><p class="value">{r['dose_diaria']:g}</p></div>
                    <div><p class="label">Restam</p><p class="value">{int(d_restantes)}d</p></div>
                    <div><p class="label">Fim</p><p class="value">{data_f.strftime('%d/%m/%Y')}</p></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.admin:
                with st.expander(f"⚙️ Ajustar {r['nome']}"):
                    # CORREÇÃO: Limite de R$ 1.000.000,00 para não travar com valores altos
                    v_add = st.number_input("Adicionar Qtd", 0.0, 100000.0, 30.0, key=f"add_{r['id']}")
                    v_prc = st.number_input("Novo Preço R$", 0.0, 1000000.0, float(r['preco']), key=f"prc_{r['id']}")
                    
                    if st.button("Confirmar Ajuste", key=f"btn_{r['id']}", use_container_width=True):
                        nova_qtd = float(est_at + v_add)
                        dt_iso = datetime.now().strftime('%Y-%m-%d')
                        res_p = requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, 
                                               json={"qtd_total": nova_qtd, "data_inicio": dt_iso, "preco": float(v_prc)})
                        
                        if res_p.status_code in [200, 201, 204]:
                            requests.post(f"{URL_BASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(v_prc), "data_compra": dt_iso})
                            st.success("✅ Atualizado!")
                            st.cache_data.clear(); time.sleep(1); st.rerun()
                        else: st.error(f"Erro no banco: {res_p.status_code}")

elif aba == "Financeiro":
    st.subheader("📊 Análise Financeira")
    df_r, df_c = buscar_dados("remedios"), buscar_dados("consultas")
    
    c1, c2 = st.columns(2)
    t_rem = df_r['preco'].sum() if not df_r.empty else 0
    t_con = df_c['valor'].sum() if not df_c.empty else 0
    c1.metric("Total Remédios", f"R$ {t_rem:,.2f}")
    c2.metric("Total Consultas", f"R$ {t_con:,.2f}")

    f_gastos = []
    if not df_r.empty:
        tr = df_r[['data_inicio', 'preco']].copy().rename(columns={'data_inicio': 'Data', 'preco': 'valor'})
        tr['Tipo'] = 'Remédios'; f_gastos.append(tr)
    if not df_c.empty:
        tc = df_c[['data_consulta', 'valor']].copy().rename(columns={'data_consulta': 'Data'})
        tc['Tipo'] = 'Consultas'; f_gastos.append(tc)
    
    if f_gastos:
        df_f = pd.concat(f_gastos)
        df_f['Mês'] = df_f['Data'].dt.strftime('%m/%Y')
        st.bar_chart(df_f.groupby(['Mês', 'Tipo'])['valor'].sum().reset_index(), x="Mês", y="valor", color="Tipo")

elif aba == "Consultas":
    st.subheader("🩺 Histórico")
    df = buscar_dados("consultas")
    if not df.empty:
        for _, c in df.iterrows():
            st.info(f"📅 **{c['data_consulta'].strftime('%d/%m/%Y')}** | {c['medico']} | R$ {float(c['valor']):,.2f}")

elif aba == "Cadastrar":
    if st.session_state.admin:
        tipo = st.radio("Cadastrar:", ["Remédio", "Consulta"], horizontal=True)
        dt_iso = datetime.now().strftime('%Y-%m-%d')
        with st.form("f_cad", clear_on_submit=True):
            if tipo == "Remédio":
                n = st.text_input("Nome")
                q = st.number_input("Quantidade Total", 0.0, step=0.5)
                d = st.number_input("Dose Diária", 0.0, step=0.5)
                p = st.number_input("Preço R$", 0.0, max_value=1000000.0)
                if st.form_submit_button("SALVAR"):
                    if n and q > 0:
                        r = requests.post(f"{URL_BASE}remedios", headers=HEADERS, json={"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "preco": float(p), "data_inicio": dt_iso})
                        if r.status_code in [200, 201, 204]:
                            st.success("✅ Salvo!"); enviar_telegram(f"🆕 {n} cadastrado.")
                            st.cache_data.clear(); time.sleep(1); st.rerun()
                        else: st.error(f"Erro {r.status_code}")
            else:
                m = st.text_input("Médico")
                v = st.number_input("Valor R$", 0.0, max_value=1000000.0)
                dt = st.date_input("Data")
                if st.form_submit_button("SALVAR"):
                    if m:
                        r = requests.post(f"{URL_BASE}consultas", headers=HEADERS, json={"medico": m, "valor": float(v), "data_consulta": dt.strftime('%Y-%m-%d')})
                        if r.status_code in [200, 201, 204]:
                            st.success("✅ Consulta salva!"); st.cache_data.clear(); time.sleep(1); st.rerun()

elif aba == "Remover":
    if st.session_state.admin:
        t_rem = st.selectbox("Tabela:", ["remedios", "consultas"])
        df_rem = buscar_dados(t_rem)
        if not df_rem.empty:
            c_nm = 'nome' if t_rem == 'remedios' else 'medico'
            i_rem = st.selectbox("Item:", df_rem[c_nm].tolist())
            if st.button("🗑️ EXCLUIR", type="primary", use_container_width=True):
                id_i = df_rem[df_rem[c_nm] == i_rem]['id'].values[0]
                r = requests.delete(f"{URL_BASE}{t_rem}?id=eq.{id_i}", headers=HEADERS)
                if r.status_code in [200, 204]:
                    st.success("✅ Removido!"); st.cache_data.clear(); time.sleep(1); st.rerun()
