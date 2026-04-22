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

# CSS BLINDADO - PARA VISIBILIDADE TOTAL (FORÇA LETRA PRETA EM TUDO)
st.markdown("""
    <style>
    /* 1. Força fundo branco em toda a aplicação */
    .stApp, [data-testid="stVerticalBlock"], [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
    }
    
    /* 2. FORÇA TODAS AS LETRAS PARA PRETO ABSOLUTO */
    * {
        color: #000000 !important;
    }

    /* 3. Garante que títulos e textos de expander sejam legíveis */
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #000000 !important;
        font-weight: 600 !important;
    }

    /* 4. Estilo dos Cards com fundo levemente cinza para destacar do branco */
    .card { 
        background-color: #F1F3F4 !important; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 10px solid #1A237E; 
        margin-bottom: 12px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: #000000 !important;
    }

    /* 5. Ajuste para os inputs de texto e números (fundo claro, letra preta) */
    input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* 6. Sidebar (Menu lateral) - Mantemos escuro mas com texto claro para contraste */
    [data-testid="stSidebar"] * {
        color: #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CONTROLE DE ACESSO ---
if "admin" not in st.session_state: st.session_state.admin = False
with st.sidebar:
    st.header("🔐 Acesso")
    if not st.session_state.admin:
        pw = st.text_input("Senha", type="password")
        if st.button("Liberar"):
            if pw == SENHA_ADM: 
                st.session_state.admin = True
                st.cache_data.clear()
                st.rerun()
            else: st.error("Senha Incorreta")
    else:
        st.success("Modo Edição Ativo")
        if st.button("Sair"): 
            st.session_state.admin = False
            st.cache_data.clear()
            st.rerun()

menu = st.sidebar.radio("Navegação", ["📊 Estoque", "🩺 Histórico Médico", "💰 Financeiro", "➕ Cadastro", "🗑️ Remover"])

# --- 5. TELAS ---

if menu == "📊 Estoque":
    st.header("💊 Estoque de Medicamentos")
    df = api_get("remedios")
    if df.empty: 
        st.info("Nenhum remédio cadastrado.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            dias_p = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_p * r['dose_diaria'])))
            dias_r = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            
            with st.expander(f"📦 {r['nome'].upper()} - Restam {estoque_atual} un."):
                st.progress(min(1.0, max(0.0, estoque_atual / r['qtd_total'])))
                
                cor_status = "#D32F2F" if dias_r <= 7 else "#1B5E20"
                st.markdown(f"""
                    <div class="card">
                        <b style="font-size: 18px;">Status do Medicamento:</b><br>
                        <span style="color:{cor_status}; font-size: 20px; font-weight: 800;">
                            {estoque_atual} unidades (Aprox. {dias_r} dias)
                        </span><br>
                        <span>Previsão de Término: <b>{(hoje + timedelta(days=dias_r)).strftime('%d/%m/%Y')}</b></span>
                    </div>
                """, unsafe_allow_html=True)

                if st.session_state.admin:
                    st.write("---")
                    adicao = st.number_input(f"Somar unidades ao {r['nome']}", min_value=1, value=30, key=f"add_{r['id']}")
                    if st.button("Confirmar Reabastecimento", key=f"btn_{r['id']}"):
                        nova_qtd = estoque_atual + adicao
                        api_patch("remedios", r['id'], {"qtd_total": int(nova_qtd), "data_inicio": str(hoje.date())})
                        api_post("compras", {"nome_remedio": r['nome'], "valor": float(r['preco']), "data_compra": str(hoje.date())})
                        st.success("Estoque Atualizado!")
                        time.sleep(1); st.cache_data.clear(); st.rerun()

elif menu == "🩺 Histórico Médico":
    st.header("🩺 Consultas e Exames")
    df_cons = api_get("consultas")
    if not df_cons.empty:
        df_v = df_cons.copy()
        df_v['data_consulta'] = df_v['data_consulta'].dt.strftime('%d/%m/%Y')
        for _, c in df_v.iterrows():
            st.markdown(f"""
                <div class="card">
                    <b style="font-size:18px;">Data: {c['data_consulta']}</b><br>
                    <b>Médico:</b> {c['medico']}<br>
                    <b>Investimento: R$ {float(c.get('valor', 0)):.2f}</b>
                </div>
            """, unsafe_allow_html=True)
    else: st.info("Nenhuma consulta registrada.")

elif menu == "💰 Financeiro":
    st.header("💰 Resumo de Gastos")
    df_compras = api_get("compras")
    df_consultas = api_get("consultas")
    tr = df_compras['valor'].sum() if not df_compras.empty else 0
    tc = df_consultas['valor'].sum() if not df_consultas.empty else 0
    
    st.markdown(f"""
        <div class="card" style="border-left: 10px solid #2E7D32; text-align: center;">
            <h2 style="margin:0;">Total Geral: R$ {tr + tc:.2f}</h2>
            <p>Remédios: R$ {tr:.2f} | Consultas: R$ {tc:.2f}</p>
        </div>
    """, unsafe_allow_html=True)

elif menu == "➕ Cadastro":
    if not st.session_state.admin: st.warning("Acesse com a senha para realizar cadastros.")
    else:
        tipo = st.selectbox("O que deseja cadastrar?", ["Remédio", "Consulta"])
        with st.form("form_cadastro"):
            if tipo == "Remédio":
                n = st.text_input("Nome")
                q = st.number_input("Qtd total na caixa", value=30)
                d = st.number_input("Dose por dia (Ex: 1.0 ou 0.5)", value=1.0)
                p = st.number_input("Preço pago na caixa", value=0.0)
                if st.form_submit_button("Salvar"):
                    api_post("remedios", {"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    api_post("compras", {"nome_remedio":n,"valor":float(p),"data_compra":str(datetime.now().date())})
                    st.success("Cadastrado com sucesso!"); time.sleep(1); st.cache_data.clear(); st.rerun()
            else:
                m = st.text_input("Médico / Especialidade")
                v = st.number_input("Valor pago", value=0.0)
                dt = st.date_input("Data")
                if st.form_submit_button("Salvar"):
                    api_post("consultas", {"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    st.success("Consulta Salva!"); time.sleep(1); st.cache_data.clear(); st.rerun()

elif menu == "🗑️ Remover":
    if not st.session_state.admin: st.warning("Acesso restrito.")
    else:
        tab = st.selectbox("Onde deseja excluir?", ["remedios", "consultas", "compras"])
        df_del = api_get(tab)
        if not df_del.empty:
            col = 'nome' if tab == 'remedios' else 'medico' if tab == 'consultas' else 'nome_remedio'
            item = st.selectbox("Escolha o item para deletar:", df_del[col].tolist())
            id_it = df_del[df_del[col] == item]['id'].values[0]
            if st.button("DELETAR AGORA"):
                api_delete(tab, id_it)
                st.success("Removido com sucesso!"); time.sleep(1); st.cache_data.clear(); st.rerun()
