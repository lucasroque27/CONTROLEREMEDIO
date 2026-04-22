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

# --- 3. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Saúde Família", page_icon="💊", layout="centered")

# CSS REFORÇADO PARA VISIBILIDADE NO CELULAR
st.markdown("""
    <style>
    /* Força o fundo da página para um cinza muito claro */
    .stApp { background-color: #F0F2F5; }
    
    /* Estilo dos Títulos Principais - AZUL ESCURO FORTE */
    h1, h2, h3 { color: #001A3D !important; font-weight: 800 !important; }
    
    /* Texto dentro dos expanders e labels */
    .stMarkdown p, label { color: #121212 !important; font-weight: 500; }

    /* Cards Brancos com texto preto para garantir leitura */
    .card { 
        background-color: #FFFFFF !important; 
        padding: 18px; 
        border-radius: 12px; 
        border-left: 8px solid #1A237E; 
        margin-bottom: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: #000000 !important;
    }
    
    /* Estilo para as métricas de dinheiro */
    .metric-card { 
        background: #FFFFFF !important; 
        padding: 20px; 
        border-radius: 12px; 
        text-align: center; 
        border: 2px solid #2E7D32; 
        margin-bottom: 20px;
        color: #000000 !important;
    }
    
    /* Forçar cor preta em textos de ajuda */
    small { color: #333333 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LOGIN ---
if "admin" not in st.session_state: st.session_state.admin = False
with st.sidebar:
    st.markdown("<h2 style='color:white;'>🔐 Acesso</h2>", unsafe_allow_html=True)
    if not st.session_state.admin:
        pw = st.text_input("Senha", type="password")
        if st.button("Liberar"):
            if pw == SENHA_ADM: st.session_state.admin = True; st.rerun()
            else: st.error("Senha Incorreta")
    else:
        st.success("Modo Edição Ativo")
        if st.button("Sair"): st.session_state.admin = False; st.rerun()

menu = st.sidebar.radio("Navegação", ["📊 Estoque", "🩺 Consultas", "💰 Financeiro", "➕ Cadastro", "🗑️ Remover"])

# --- 5. TELAS ---

if menu == "📊 Estoque":
    st.markdown("<h2>💊 Estoque de Medicamentos</h2>", unsafe_allow_html=True)
    df = api_get("remedios")
    if df.empty: 
        st.info("Nenhum remédio cadastrado.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            dias_p = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_p * r['dose_diaria'])))
            dias_r = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            
            # Título do remédio em negrito e preto
            with st.expander(f"📦 {r['nome'].upper()} - {estoque_atual} un. restantes"):
                st.progress(min(1.0, max(0.0, estoque_atual / r['qtd_total'])))
                
                cor_status = "#D32F2F" if dias_r <= 7 else "#1B5E20"
                st.markdown(f"""
                    <div class="card">
                        <b style="font-size: 18px; color: #000;">Status Atual:</b><br>
                        <span style="color:{cor_status}; font-size: 22px; font-weight: bold;">
                            {estoque_atual} unidades ({dias_r} dias)
                        </span><br>
                        <span style="color:#333;">Previsão de Término: <b>{(hoje + timedelta(days=dias_r)).strftime('%d/%m/%Y')}</b></span>
                    </div>
                """, unsafe_allow_html=True)

                if st.session_state.admin:
                    st.markdown("<b style='color:black;'>📥 Reabastecer:</b>", unsafe_allow_html=True)
                    adicao = st.number_input("Somar mais quantas unidades?", min_value=1, value=30, key=f"add_{r['id']}")
                    if st.button("Confirmar Soma", key=f"btn_{r['id']}"):
                        nova_qtd = estoque_atual + adicao
                        api_patch("remedios", r['id'], {"qtd_total": int(nova_qtd), "data_inicio": str(hoje.date())})
                        api_post("compras", {"nome_remedio": r['nome'], "valor": float(r['preco']), "data_compra": str(hoje.date())})
                        st.success("Estoque atualizado!")
                        time.sleep(1)
                        st.cache_data.clear()
                        st.rerun()

elif menu == "🩺 Consultas":
    st.markdown("<h2>🩺 Histórico Médico</h2>", unsafe_allow_html=True)
    df_cons = api_get("consultas")
    if not df_cons.empty:
        df_v = df_cons.copy()
        df_v['data_consulta'] = df_v['data_consulta'].dt.strftime('%d/%m/%Y')
        for _, c in df_v.iterrows():
            st.markdown(f"""
                <div class="card">
                    <b style="color:#1A237E; font-size:18px;">{c['data_consulta']}</b><br>
                    <b style="color:#000;">Médico:</b> {c['medico']}<br>
                    <b style="color:#2E7D32;">Valor: R$ {float(c.get('valor', 0)):.2f}</b>
                </div>
            """, unsafe_allow_html=True)
    else: st.info("Nenhuma consulta registrada.")

elif menu == "💰 Financeiro":
    st.markdown("<h2>💰 Gastos Totais</h2>", unsafe_allow_html=True)
    df_compras = api_get("compras")
    df_consultas = api_get("consultas")
    tr = df_compras['valor'].sum() if not df_compras.empty else 0
    tc = df_consultas['valor'].sum() if not df_consultas.empty else 0
    
    st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; color:#1B5E20;">Total: R$ {tr + tc:.2f}</h3>
            <p style="color:#444;">Remédios: R$ {tr:.2f} | Consultas: R$ {tc:.2f}</p>
        </div>
    """, unsafe_allow_html=True)

elif menu == "➕ Cadastro":
    if not st.session_state.admin: st.warning("Acesse com a senha para cadastrar.")
    else:
        tipo = st.selectbox("O que deseja registrar?", ["Medicamento", "Consulta"])
        with st.form("cadastro"):
            if tipo == "Medicamento":
                n = st.text_input("Nome do Remédio")
                q = st.number_input("Quantidade na Caixa", value=30)
                d = st.number_input("Dose por Dia", value=1.0)
                p = st.number_input("Preço da Caixa", value=0.0)
                if st.form_submit_button("Salvar Medicamento"):
                    api_post("remedios", {"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    api_post("compras", {"nome_remedio":n,"valor":float(p),"data_compra":str(datetime.now().date())})
                    st.success("Salvo!")
                    time.sleep(1); st.cache_data.clear(); st.rerun()
            else:
                m = st.text_input("Nome do Médico")
                v = st.number_input("Valor da Consulta", value=0.0)
                dt = st.date_input("Data da Consulta")
                if st.form_submit_button("Salvar Consulta"):
                    api_post("consultas", {"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    st.success("Consulta registrada!")
                    time.sleep(1); st.cache_data.clear(); st.rerun()

elif menu == "🗑️ Remover":
    if not st.session_state.admin: st.warning("Acesso restrito ao administrador.")
    else:
        tabela = st.selectbox("Selecione a categoria:", ["remedios", "consultas", "compras"])
        df_del = api_get(tabela)
        if not df_del.empty:
            col = 'nome' if tabela == 'remedios' else 'medico' if tabela == 'consultas' else 'nome_remedio'
            item = st.selectbox("Selecione o item para excluir:", df_del[col].tolist())
            id_it = df_del[df_del[col] == item]['id'].values[0]
            if st.button("EXCLUIR PERMANENTEMENTE"):
                api_delete(tabela, id_it)
                st.success("Item removido!")
                time.sleep(1); st.cache_data.clear(); st.rerun()
