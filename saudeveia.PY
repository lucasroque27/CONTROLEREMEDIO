import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import time

# --- 1. CONFIGURAÇÕES SUPABASE ---
URL_SUPABASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"

HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

SENHA_ADM = "1234"
TELEGRAM_TOKEN = "8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM"
LISTA_IDS = ["5256921022"]

# --- 2. FUNÇÕES DE COMUNICAÇÃO ---
def api_get(tabela):
    try:
        res = requests.get(f"{URL_SUPABASE}{tabela}?select=*&order=id.desc", headers=HEADERS)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            for col in ['data_inicio', 'data_consulta', 'data_compra']:
                if not df.empty and col in df.columns:
                    df[col] = pd.to_datetime(df[col])
            return df
    except: pass
    return pd.DataFrame()

def api_post(tabela, dados):
    res = requests.post(URL_SUPABASE + tabela, headers=HEADERS, json=dados)
    return res.status_code

def api_patch(tabela, id_item, dados):
    res = requests.patch(f"{URL_SUPABASE}{tabela}?id=eq.{id_item}", headers=HEADERS, json=dados)
    return res.status_code

def api_delete(tabela, id_item):
    requests.delete(f"{URL_SUPABASE}{tabela}?id=eq.{id_item}", headers=HEADERS)

def enviar_telegram(msg):
    for cid in LISTA_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try: requests.post(url, json={"chat_id": cid, "text": msg, "parse_mode": "Markdown"})
        except: pass

# --- 3. INTERFACE E CSS ---
st.set_page_config(page_title="Saúde Família Cloud", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .card { background: white; padding: 15px; border-radius: 12px; border-left: 5px solid #1A237E; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .metric-card { background: #E8F5E9; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #A5D6A7; margin-bottom: 20px; }
    .title-text { color: #1A237E; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ACESSO ---
if "admin" not in st.session_state: st.session_state.admin = False
with st.sidebar:
    st.title("🔐 Gestão")
    if not st.session_state.admin:
        pw = st.text_input("Senha", type="password")
        if st.button("Liberar"):
            if pw == SENHA_ADM: st.session_state.admin = True; st.rerun()
            else: st.error("Senha Incorreta")
    else:
        st.success("✨ Modo Edição Ativo")
        if st.button("Sair"): st.session_state.admin = False; st.rerun()

menu = st.sidebar.radio("Navegação", ["📊 Estoque", "🩺 Consultas", "💰 Controle Financeiro", "➕ Novo Cadastro", "🗑️ Remover"])

# --- 5. TELAS ---

if menu == "📊 Estoque":
    st.markdown("<h2 class='title-text'>💊 Estoque de Medicamentos</h2>", unsafe_allow_html=True)
    
    # AQUI ESTÁ A CHAVE: Buscamos APENAS da tabela 'remedios'
    df = api_get("remedios")
    
    if df.empty:
        st.info("Nenhum remédio cadastrado.")
    else:
        hoje = datetime.now()
        alertas = []
        for _, r in df.iterrows():
            # Cálculo matemático do estoque
            dias_p = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_p * r['dose_diaria'])))
            dias_r = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            
            # Interface com Expander para cada remédio
            with st.expander(f"💊 {r['nome'].upper()} - Restam {estoque_atual} un."):
                st.progress(min(1.0, max(0.0, estoque_atual / r['qtd_total'])))
                
                cor = "#D32F2F" if dias_r <= 7 else "#2E7D32"
                st.markdown(f"""<div class="card">
                    <span style="color:{cor}; font-weight:bold;">Status: {estoque_atual} un. ({dias_r} dias)</span><br>
                    <span style="color:#555;">🗓️ Previsão de Término: {(hoje + timedelta(days=dias_r)).strftime('%d/%m/%Y')}</span>
                </div>""", unsafe_allow_html=True)

                # --- FUNÇÃO DE SOMAR ESTOQUE (ADMIN) ---
                if st.session_state.admin:
                    st.write("---")
                    st.write("**📥 Adicionar Nova Caixa**")
                    col1, col2 = st.columns(2)
                    with col1:
                        adicao = st.number_input("Qtd para somar", min_value=1, value=30, key=f"add_{r['id']}")
                    with col2:
                        preco_novo = st.number_input("Preço pago (R$)", min_value=0.0, value=float(r['preco']), key=f"prc_{r['id']}")
                    
                    if st.button(f"Confirmar Soma de {r['nome']}", key=f"btn_{r['id']}"):
                        nova_qtd_total = estoque_atual + adicao
                        dados_up = {
                            "qtd_total": int(nova_qtd_total),
                            "data_inicio": str(hoje.date()), # Reinicia o contador para hoje
                            "preco": float(preco_novo)
                        }
                        if api_patch("remedios", r['id'], dados_up) in [200, 204]:
                            # Registra a compra no financeiro
                            api_post("compras", {"nome_remedio": r['nome'], "valor": float(preco_novo), "data_compra": str(hoje.date()), "qtd_comprada": int(adicao)})
                            st.success("Estoque somado com sucesso!")
                            time.sleep(1); st.rerun()

            if dias_r <= 7: alertas.append(f"🚨 {r['nome']}")
        
        if alertas and "avisado" not in st.session_state:
            enviar_telegram("📢 *ALERTA DE REPOSIÇÃO:* " + ", ".join(alertas))
            st.session_state.avisado = True

elif menu == "🩺 Consultas":
    st.markdown("<h2 class='title-text'>🩺 Histórico de Consultas</h2>", unsafe_allow_html=True)
    df_cons = api_get("consultas")
    if not df_cons.empty:
        df_v = df_cons.copy()
        df_v['data_consulta'] = df_v['data_consulta'].dt.strftime('%d/%m/%Y')
        for _, c in df_v.iterrows():
            st.markdown(f"""<div class="card">
                <b style="color:#1A237E;">{c['data_consulta']} - {c['medico']}</b><br>
                <span><b>Especialidade:</b> {c.get('especialidade', 'Geral')}</span><br>
                <span><b>Local:</b> {c.get('local', 'N/I')}</span><br>
                <b style="color:#2E7D32;">Valor Pago: R$ {float(c.get('valor', 0)):.2f}</b>
            </div>""", unsafe_allow_html=True)
    else: st.info("Nenhuma consulta registrada.")

elif menu == "💰 Controle Financeiro":
    st.markdown("<h2 class='title-text'>💰 Gastos Totais</h2>", unsafe_allow_html=True)
    df_compras = api_get("compras")
    df_consultas = api_get("consultas")
    
    tr = df_compras['valor'].sum() if not df_compras.empty else 0
    tc = df_consultas['valor'].sum() if not df_consultas.empty and 'valor' in df_consultas.columns else 0
    
    st.markdown(f"""<div class="metric-card">
        <h3>Investimento Total: R$ {tr + tc:.2f}</h3>
        <p>Medicamentos: R$ {tr:.2f} | Consultas: R$ {tc:.2f}</p>
    </div>""", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🛒 Compras", "👨‍⚕️ Médicos"])
    with tab1:
        if not df_compras.empty:
            df_c = df_compras.copy(); df_c['data_compra'] = df_c['data_compra'].dt.strftime('%d/%m/%Y')
            st.table(df_c[['data_compra', 'nome_remedio', 'valor']])
    with tab2:
        if not df_consultas.empty:
            df_cf = df_consultas.copy(); df_cf['data_consulta'] = df_cf['data_consulta'].dt.strftime('%d/%m/%Y')
            st.table(df_cf[['data_consulta', 'medico', 'valor']])

elif menu == "➕ Novo Cadastro":
    if not st.session_state.admin: st.warning("Acesse com a senha.")
    else:
        tipo = st.selectbox("O que deseja registrar?", ["Medicamento", "Consulta"])
        with st.form("f_cadastro"):
            if tipo == "Medicamento":
                n, q = st.text_input("Nome"), st.number_input("Qtd na Caixa", min_value=1, value=30)
                d, p = st.number_input("Dose Diária", value=1.0), st.number_input("Preço R$", min_value=0.0)
                dt = st.date_input("Data da Compra")
                if st.form_submit_button("Salvar Registro"):
                    api_post("remedios", {"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(dt)})
                    api_post("compras", {"nome_remedio":n,"valor":float(p),"data_compra":str(dt),"qtd_comprada":int(q)})
                    st.success("Salvo com sucesso!"); time.sleep(1); st.rerun()
            else:
                m, e = st.text_input("Médico"), st.text_input("Especialidade")
                l, v = st.text_input("Local"), st.number_input("Valor R$", min_value=0.0)
                dt_c = st.date_input("Data da Consulta")
                if st.form_submit_button("Agendar Consulta"):
                    api_post("consultas", {"medico":m, "especialidade":e, "local":l, "data_consulta":str(dt_c), "valor":float(v)})
                    st.success("Consulta registrada!"); time.sleep(1); st.rerun()

elif menu == "🗑️ Remover":
    if not st.session_state.admin: st.warning("Acesse com a senha.")
    else:
        tabela = st.selectbox("Categoria:", ["remedios", "consultas", "compras"])
        df_del = api_get(tabela)
        if not df_del.empty:
            col = 'nome' if tabela == 'remedios' else 'medico' if tabela == 'consultas' else 'nome_remedio'
            item = st.selectbox("Selecione para excluir:", df_del[col].tolist())
            id_it = df_del[df_del[col] == item]['id'].values[0]
            if st.button("EXCLUIR"):
                api_delete(tabela, id_it); st.success("Excluído!"); time.sleep(1); st.rerun()