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
    return requests.post(URL_SUPABASE + tabela, headers=HEADERS, json=dados).status_code

def api_patch(tabela, id_item, dados):
    return requests.patch(f"{URL_SUPABASE}{tabela}?id=eq.{id_item}", headers=HEADERS, json=dados).status_code

def api_delete(tabela, id_item):
    requests.delete(f"{URL_SUPABASE}{tabela}?id=eq.{id_item}", headers=HEADERS)

# --- 3. ESTILO CSS (LETRA BRANCA NO MENU / PRETA NO CORPO) ---
st.set_page_config(page_title="Saúde Família", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    /* FUNDO DO APP */
    .stApp { background-color: #FFFFFF !important; }

    /* MENU LATERAL (SIDEBAR) */
    [data-testid="stSidebar"] {
        background-color: #0A192F !important;
        color: #FFFFFF !important;
    }
    
    /* FORÇA LETRA BRANCA EM TUDO NA SIDEBAR */
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    /* BOTÃO DE MENU (HEADER) */
    header[data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
        visibility: visible !important;
    }

    /* CARDS DE REMÉDIO NA TELA PRINCIPAL */
    .med-card {
        background-color: #F8F9FA !important;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #E2E8F0;
        border-left: 12px solid #3B82F6;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }

    /* TEXTO NA TELA PRINCIPAL (SEMPRE PRETO) */
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label, .stMarkdown {
        color: #000000 !important;
        font-weight: 600;
    }

    /* BOTÕES */
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        background-color: #3B82F6 !important;
        color: white !important;
        font-weight: bold;
        height: 3em;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🏥 Gestão Saúde</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    if "admin" not in st.session_state: st.session_state.admin = False
    
    if not st.session_state.admin:
        st.markdown("🔒 **Acesso ADM**")
        pw = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if pw == SENHA_ADM:
                st.session_state.admin = True
                st.rerun()
            else: st.error("Senha Incorreta")
    else:
        st.success("✨ Modo Edição Ativo")
        if st.button("Sair do Modo ADM"):
            st.session_state.admin = False
            st.rerun()
    
    st.markdown("---")
    menu = st.radio("Navegação", ["📊 Estoque", "🩺 Consultas", "💰 Financeiro", "➕ Cadastro", "🗑️ Remover"])

# --- 5. LÓGICA DAS TELAS ---

if menu == "📊 Estoque":
    st.title("💊 Controle de Medicamentos")
    df = api_get("remedios")
    if df.empty:
        st.info("Nenhum remédio cadastrado.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            # CÁLCULO DO CONSUMO ATÉ AGORA
            dias_passados = (hoje - r['data_inicio']).days
            consumo_real = dias_passados * r['dose_diaria']
            estoque_atual = max(0, int(r['qtd_total'] - consumo_real))
            
            # CÁLCULO DE QUANTO TEMPO DURA
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)
            
            st.markdown(f"""
                <div class="med-card">
                    <span style="font-size: 1.4em; color: #000000;"><b>{r['nome'].upper()}</b></span><br><br>
                    <p style="margin:0; font-size: 1.1em;">📦 Restam: <b>{estoque_atual} comprimidos</b></p>
                    <p style="margin:0;">🕒 Dose diária: <b>{r['dose_diaria']} un.</b></p>
                    <p style="margin:0;">⏳ Duração: <b>{dias_restantes} dias</b></p>
                    <p style="margin-top:10px; font-size: 1.2em; color: {'#CC0000' if dias_restantes < 5 else '#006600'} !important;">
                        📅 Acaba em: <b>{data_fim.strftime('%d/%m/%Y')}</b>
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.admin:
                with st.expander(f"🔄 Repor {r['nome']}"):
                    with st.form(f"form_{r['id']}"):
                        nova_qtd = st.number_input("Qtd comprada", min_value=1, value=30)
                        novo_valor = st.number_input("Preço da nova caixa", min_value=0.0, value=float(r['preco']))
                        if st.form_submit_button("Confirmar Reposição"):
                            estoque_novo = estoque_atual + nova_qtd
                            # Atualiza estoque e preço no banco
                            api_patch("remedios", r['id'], {"qtd_total": int(estoque_novo), "data_inicio": str(hoje.date()), "preco": float(novo_valor)})
                            # Registra no histórico de compras
                            api_post("compras", {"nome_remedio": r['nome'], "valor": float(novo_valor), "data_compra": str(hoje.date())})
                            st.success("Estoque atualizado!"); time.sleep(1); st.cache_data.clear(); st.rerun()

elif menu == "🩺 Consultas":
    st.title("🩺 Histórico de Consultas")
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            st.markdown(f"""
                <div class="med-card" style="border-left-color: #10B981;">
                    <p style="margin:0;">📅 Data: {c['data_consulta'].strftime('%d/%m/%Y')}</p>
                    <p style="margin:0; font-size: 1.2em;"><b>Dr(a). {c['medico']}</b></p>
                    <p style="margin:0; color: #166534;">Valor: R$ {float(c.get('valor', 0)):.2f}</p>
                </div>
            """, unsafe_allow_html=True)

elif menu == "💰 Financeiro":
    st.title("💰 Controle Financeiro")
    df_r = api_get("compras")
    df_c = api_get("consultas")
    t1 = df_r['valor'].sum() if not df_r.empty else 0
    t2 = df_c['valor'].sum() if not df_c.empty else 0
    
    st.markdown(f"""
        <div class="med-card" style="text-align: center; border-left: none; border-top: 8px solid #3B82F6;">
            <p style="margin:0;">Total Gasto Acumulado</p>
            <h1 style="color: #000000 !important; margin:0;">R$ {t1+t2:.2f}</h1>
            <p style="margin-top:10px;">Remédios: R$ {t1:.2f} | Consultas: R$ {t2:.2f}</p>
        </div>
    """, unsafe_allow_html=True)
    
    if not df_r.empty:
        st.subheader("🛒 Histórico de Compras")
        st.dataframe(df_r[['data_compra', 'nome_remedio', 'valor']], use_container_width=True)

elif menu == "➕ Cadastro":
    if not st.session_state.admin:
        st.warning("🔒 Acesse o modo ADM no menu para cadastrar.")
    else:
        tipo = st.selectbox("O que deseja cadastrar?", ["Medicamento", "Consulta"])
        with st.form("cad_geral"):
            if tipo == "Medicamento":
                n = st.text_input("Nome do Remédio")
                q = st.number_input("Quantidade na Caixa", value=30)
                d = st.number_input("Doses por dia", value=1.0)
                p = st.number_input("Preço da Caixa", value=0.0)
                if st.form_submit_button("Salvar Medicamento"):
                    api_post("remedios", {"nome":n, "qtd_total":int(q), "dose_diaria":float(d), "preco":float(p), "data_inicio":str(datetime.now().date())})
                    api_post("compras", {"nome_remedio":n, "valor":float(p), "data_compra":str(datetime.now().date())})
                    st.success("Salvo!"); time.sleep(1); st.cache_data.clear(); st.rerun()
            else:
                m = st.text_input("Nome do Médico / Especialidade")
                v = st.number_input("Valor da Consulta", value=0.0)
                dt = st.date_input("Data da Consulta")
                if st.form_submit_button("Registrar Consulta"):
                    api_post("consultas", {"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    st.success("Registrado!"); time.sleep(1); st.cache_data.clear(); st.rerun()

elif menu == "🗑️ Remover":
    if not st.session_state.admin:
        st.warning("🔒 Acesso restrito ao Administrador.")
    else:
        st.title("🗑️ Excluir Registros")
        tab = st.selectbox("Escolha a categoria:", ["remedios", "consultas", "compras"])
        df_d = api_get(tab)
        if not df_d.empty:
            col_ref = 'nome' if tab == 'remedios' else 'medico' if tab == 'consultas' else 'nome_remedio'
            item_del = st.selectbox("Selecione o item para apagar:", df_d[col_ref].tolist())
            id_del = df_d[df_d[col_ref] == item_del]['id'].values[0]
            if st.button("❌ APAGAR DEFINITIVAMENTE"):
                api_delete(tab, id_del)
                st.success("Removido!"); time.sleep(1); st.cache_data.clear(); st.rerun()
