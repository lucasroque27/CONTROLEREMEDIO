import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import time

# --- 1. CONFIGURAÇÕES E CONEXÃO ---
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

@st.cache_data(ttl=2)
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

# --- 2. LAYOUT ---
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
        pw = st.text_input("Senha ADM", type="password", key="login_pass")
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
    st.subheader("📋 Status dos Medicamentos")
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
                    <div><p class="label">Estoque</p><p class="value">{est_at:g}</p></div>
                    <div><p class="label">Dose/Dia</p><p class="value">{r['dose_diaria']:g}</p></div>
                    <div><p class="label">Dias</p><p class="value">{int(d_restantes)}d</p></div>
                    <div><p class="label">Previsão Fim</p><p class="value">{data_f.strftime('%d/%m/%Y')}</p></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.admin:
                with st.expander(f"⚙️ Ajustar {r['nome']}"):
                    c1, c2 = st.columns(2)
                    v_add = c1.number_input("Adicionar Qtd", 0.0, 1000.0, 30.0, key=f"add_{r['id']}")
                    v_prc = c2.number_input("Preço Atual R$", 0.0, 50000.0, float(r['preco']), key=f"prc_{r['id']}")
                    if st.button("Salvar Ajuste", key=f"btn_{r['id']}", use_container_width=True):
                        nova_qtd = float(est_at + v_add)
                        dt_hoje = datetime.now().strftime('%Y-%m-%d')
                        
                        # Correção Erro 400: PATCH com tipos convertidos
                        res_p = requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, 
                                               json={"qtd_total": nova_qtd, "data_inicio": dt_hoje, "preco": float(v_prc)})
                        
                        requests.post(f"{URL_BASE}compras", headers=HEADERS, 
                                      json={"nome_remedio": r['nome'], "valor": float(v_prc), "data_compra": dt_hoje})
                        
                        if res_p.status_code in [200, 201, 204]:
                            st.success("✅ Estoque Atualizado!")
                            st.cache_data.clear(); time.sleep(1); st.rerun()
                        else:
                            st.error(f"Erro 400: Verifique os dados. Status: {res_p.status_code}")

elif aba == "Financeiro":
    st.subheader("💰 Gastos Atuais")
    df_r, df_c = buscar_dados("remedios"), buscar_dados("consultas")
    f_gastos = []
    if not df_r.empty:
        temp_r = df_r[['data_inicio', 'preco']].copy()
        temp_r['Tipo'] = 'Remédios'; temp_r = temp_r.rename(columns={'data_inicio': 'Data', 'preco': 'valor'})
        f_gastos.append(temp_r)
    if not df_c.empty:
        temp_c = df_c[['data_consulta', 'valor']].copy()
        temp_c['Tipo'] = 'Consultas'; temp_c = temp_c.rename(columns={'data_consulta': 'Data'})
        f_gastos.append(temp_c)
    
    if f_gastos:
        df_f = pd.concat(f_gastos)
        df_f['Mês'] = df_f['Data'].dt.strftime('%m/%Y')
        st.bar_chart(df_f.groupby(['Mês', 'Tipo'])['valor'].sum().reset_index(), x="Mês", y="valor", color="Tipo")
        st.metric("Total Investido (Itens Ativos)", f"R$ {df_f['valor'].sum():,.2f}")

elif aba == "Consultas":
    st.subheader("🩺 Histórico")
    df = buscar_dados("consultas")
    if not df.empty:
        for _, c in df.iterrows():
            st.info(f"📅 **{c['data_consulta'].strftime('%d/%m/%Y')}** | {c['medico']} | R$ {float(c['valor']):.2f}")

elif aba == "Cadastrar":
    if st.session_state.admin:
        tipo = st.radio("Selecione:", ["Medicamento", "Consulta"], horizontal=True)
        dt_hoje = datetime.now().strftime('%Y-%m-%d')
        
        with st.form("main_form", clear_on_submit=True):
            if tipo == "Medicamento":
                f_nome = st.text_input("Nome")
                f_qtd = st.number_input("Qtd Inicial", 0.0, step=0.5)
                f_dose = st.number_input("Dose/Dia", 0.0, step=0.5)
                f_preco = st.number_input("Preço", 0.0)
                if st.form_submit_button("FINALIZAR CADASTRO"):
                    if f_nome and f_qtd > 0:
                        pay = {"nome": f_nome, "qtd_total": float(f_qtd), "dose_diaria": float(f_dose), "preco": float(f_preco), "data_inicio": dt_hoje}
                        r = requests.post(f"{URL_BASE}remedios", headers=HEADERS, json=pay)
                        if r.status_code in [200, 201, 204]:
                            st.success(f"✅ {f_nome} salvo!"); enviar_telegram(f"🆕 Remédio: {f_nome}")
                            st.cache_data.clear(); time.sleep(1); st.rerun()
                        else: st.error(f"Erro 400 ao cadastrar. Status: {r.status_code}")
            else:
                f_med = st.text_input("Médico")
                f_vlr = st.number_input("Valor", 0.0)
                f_dat = st.date_input("Data")
                if st.form_submit_button("FINALIZAR CADASTRO"):
                    if f_med:
                        pay = {"medico": f_med, "valor": float(f_vlr), "data_consulta": f_dat.strftime('%Y-%m-%d')}
                        r = requests.post(f"{URL_BASE}consultas", headers=HEADERS, json=pay)
                        if r.status_code in [200, 201, 204]:
                            st.success("✅ Consulta salva!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                        else: st.error(f"Erro 400 ao cadastrar consulta. Status: {r.status_code}")

elif aba == "Remover":
    if st.session_state.admin:
        tab_rem = st.selectbox("Apagar de:", ["remedios", "consultas"])
        df_rem = buscar_dados(tab_rem)
        if not df_rem.empty:
            col_name = 'nome' if tab_rem == 'remedios' else 'medico'
            item_rem = st.selectbox("Qual item?", df_rem[col_name].tolist())
            if st.button("🗑️ CONFIRMAR EXCLUSÃO", type="primary", use_container_width=True):
                id_rem = df_rem[df_rem[col_name] == item_rem]['id'].values[0]
                r = requests.delete(f"{URL_BASE}{tab_rem}?id=eq.{id_rem}", headers=HEADERS)
                if r.status_code in [200, 204]:
                    st.success("✅ Excluído!"); st.cache_data.clear(); time.sleep(1); st.rerun()
