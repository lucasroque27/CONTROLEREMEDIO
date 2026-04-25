import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

# --- 1. CONFIGURAÇÕES E PILARES (Estabilidade e Conectividade) ---
URL_BASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
HEADERS = {"apikey": API_KEY, "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "Prefer": "representation"}

def enviar_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM/sendMessage", 
                      json={"chat_id": "5256921022", "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

@st.cache_data(ttl=5)
def buscar_dados(tabela):
    try:
        res = requests.get(f"{URL_BASE}{tabela}?select=*&order=id.desc", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            for col in ['data_inicio', 'data_consulta', 'data_compra']:
                if not df.empty and col in df.columns: df[col] = pd.to_datetime(df[col])
            return df
    except: pass
    return pd.DataFrame()

# --- 2. INTERFACE ---
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
    st.title("💊 Gestão")
    if not st.session_state.admin:
        pw = st.text_input("Senha ADM", type="password", key="login_pass")
        if st.button("Acessar", use_container_width=True) or (pw == "1234"):
            if pw == "1234":
                st.session_state.admin = True
                st.rerun()
    else:
        if st.button("Sair", use_container_width=True): st.session_state.admin = False; st.rerun()
    aba = st.radio("Navegação:", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"], key="nav_main")

# --- 3. TELAS ---

if aba == "Estoque":
    st.subheader("📋 Resumo de Medicamentos")
    df = buscar_dados("remedios")
    if not df.empty:
        hoje = datetime.now()
        for _, r in df.iterrows():
            dias_p = (hoje - r['data_inicio']).days
            estoque_at = max(0.0, float(r['qtd_total']) - (dias_p * float(r['dose_diaria'])))
            dias_r = float(estoque_at / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_f = hoje + timedelta(days=dias_r)
            
            st.markdown(f"""
            <div class="card">
                <div style="font-weight:bold; color:#34495e;">💊 {r['nome'].upper()}</div>
                <hr style="margin: 10px 0; border:0; border-top:1px solid #f5f5f5;">
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div><p class="label">Qtd</p><p class="value">{estoque_at:g}</p></div>
                    <div><p class="label">Dose/Dia</p><p class="value">{r['dose_diaria']:g}</p></div>
                    <div><p class="label">Restam</p><p class="value">{int(dias_r)}d</p></div>
                    <div><p class="label">Acaba em</p><p class="value">{data_f.strftime('%d/%m/%Y')}</p></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.admin:
                with st.expander(f"Ajustar {r['nome']}"):
                    c1, c2 = st.columns(2)
                    add = c1.number_input("Adicionar Qtd", 0.0, 1000.0, 30.0, key=f"add_{r['id']}")
                    prc = c2.number_input("Preço R$", 0.0, 50000.0, float(r['preco']), key=f"prc_{r['id']}")
                    if st.button("Salvar Ajuste", key=f"btn_{r['id']}"):
                        requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": estoque_at + add, "data_inicio": str(hoje.date()), "preco": prc})
                        requests.post(f"{URL_BASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": prc, "data_compra": str(hoje.date())})
                        st.cache_data.clear(); st.rerun()

elif aba == "Financeiro":
    st.subheader("💰 Controle de Gastos")
    df_r, df_c = buscar_dados("remedios"), buscar_dados("consultas")
    gastos = []
    if not df_r.empty:
        df_r['Tipo'] = 'Remédios'
        gastos.append(df_r[['data_inicio', 'preco', 'Tipo']].rename(columns={'data_inicio': 'Data', 'preco': 'valor'}))
    if not df_c.empty:
        df_c['Tipo'] = 'Consultas'
        gastos.append(df_c[['data_consulta', 'valor', 'Tipo']].rename(columns={'data_consulta': 'Data'}))
    
    if gastos:
        df_fin = pd.concat(gastos)
        df_fin['Mês'] = df_fin['Data'].dt.strftime('%m/%Y')
        st.bar_chart(df_fin.groupby(['Mês', 'Tipo'])['valor'].sum().reset_index(), x="Mês", y="valor", color="Tipo")
        st.metric("Total (Itens Ativos)", f"R$ {df_fin['valor'].sum():,.2f}")
    else: st.info("Sem dados ativos.")

elif aba == "Consultas":
    st.subheader("🩺 Consultas")
    df = buscar_dados("consultas")
    if not df.empty:
        for _, c in df.iterrows():
            st.info(f"📅 **{c['data_consulta'].strftime('%d/%m/%Y')}** | {c['medico']} | R$ {c['valor']:.2f}")

elif aba == "Cadastrar":
    if st.session_state.admin:
        sel = st.radio("O que deseja cadastrar?", ["Remédio", "Consulta"], horizontal=True, key="cad_selector")
        with st.form("form_novo_registro", clear_on_submit=True):
            if sel == "Remédio":
                n = st.text_input("Nome do Medicamento")
                q = st.number_input("Quantidade Total (Comprimidos)", 0.0, step=0.5)
                d = st.number_input("Dose Diária (Ex: 1.5)", 0.0, step=0.5)
                p = st.number_input("Preço da Embalagem R$", 0.0)
                if st.form_submit_button("Confirmar Cadastro de Remédio"):
                    if n and q > 0:
                        requests.post(f"{URL_BASE}remedios", headers=HEADERS, json={"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "preco": float(p), "data_inicio": str(datetime.now().date())})
                        enviar_telegram(f"🆕 Novo remédio: {n}")
                        st.success("Remédio cadastrado!"); st.cache_data.clear(); st.rerun()
            else:
                m = st.text_input("Médico / Clínica")
                v = st.number_input("Valor da Consulta R$", 0.0)
                dt = st.date_input("Data da Consulta")
                if st.form_submit_button("Confirmar Cadastro de Consulta"):
                    if m:
                        requests.post(f"{URL_BASE}consultas", headers=HEADERS, json={"medico": m, "valor": float(v), "data_consulta": str(dt)})
                        st.success("Consulta cadastrada!"); st.cache_data.clear(); st.rerun()
    else: st.warning("Acesse com a senha ADM para cadastrar.")

elif aba == "Remover":
    if st.session_state.admin:
        tab = st.selectbox("Apagar de:", ["remedios", "consultas"])
        df_del = buscar_dados(tab)
        if not df_del.empty:
            col = 'nome' if tab == 'remedios' else 'medico'
            item = st.selectbox("Escolha o item:", df_del[col].tolist())
            if st.button("🗑️ Remover permanentemente", type="primary"):
                id_id = df_del[df_del[col] == item]['id'].values[0]
                res = requests.delete(f"{URL_BASE}{tab}?id=eq.{id_id}", headers=HEADERS)
                if res.status_code in [200, 204]:
                    st.success(f"✅ {item} removido! O financeiro foi atualizado.")
                    st.cache_data.clear(); import time; time.sleep(1); st.rerun()
