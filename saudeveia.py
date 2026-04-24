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
SENHA_ADM = "1234"

HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. FUNÇÕES ---
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
                if not df.empty and col in df.columns:
                    df[col] = pd.to_datetime(df[col])
            return df
    except: pass
    return pd.DataFrame()

# --- 3. ESTILO CSS "USER-FRIENDLY & PRO" ---
st.set_page_config(page_title="Saúde Rock", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    /* Estilo dos Cards Principais */
    .med-card {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    
    /* Cabeçalho do Card com nome e status */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    
    .status-badge {
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
        color: white;
    }

    /* Informações de Estoque Estilizadas */
    .stock-box {
        background-color: #f8fafc;
        border-radius: 12px;
        padding: 12px;
        display: flex;
        justify-content: space-around;
        text-align: center;
        margin-top: 10px;
    }
    
    .stock-item {
        flex: 1;
    }
    
    .stock-value {
        display: block;
        font-size: 1.4rem;
        font-weight: 800;
        color: #1e293b;
    }
    
    .stock-label {
        font-size: 0.8rem;
        color: #64748b;
    }

    /* Métrica de Preço no Card */
    .price-tag {
        font-size: 0.9rem;
        color: #059669;
        font-weight: 600;
        margin-top: 5px;
    }

    /* Títulos e Textos */
    h1, h2, h3 { color: #0f172a !important; font-weight: 800 !important; }
    p, b, span { color: #334155 !important; }

    /* Botões Modernos */
    div.stButton > button {
        border-radius: 12px !important;
        background-color: #3b82f6 !important;
        height: 48px !important;
        font-weight: bold !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h1>🩺 Gestão</h1>", unsafe_allow_html=True)
    if "admin" not in st.session_state: st.session_state.admin = False
    
    if not st.session_state.admin:
        with st.form("login_form"):
            pw = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar Painel"):
                if pw == SENHA_ADM: st.session_state.admin = True; st.rerun()
                else: st.error("Incorreta")
    else:
        st.success("Administrador Ativo")
        if st.button("Encerrar Sessão"): st.session_state.admin = False; st.rerun()

    menu = st.radio("Menu Principal", ["📋 Painel de Controle", "🩺 Minhas Consultas", "💰 Gastos Detalhados", "⚙️ Cadastros", "🗑️ Apagar"])

# --- 5. TELAS ---

if menu == "📋 Painel de Controle":
    st.title("💊 Controle de Medicamentos")
    df = api_get("remedios")
    
    if df.empty:
        st.info("Nenhum dado encontrado.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            dias_passados = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_passados * r['dose_diaria'])))
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)
            
            # Lógica de Cores Semânticas
            if dias_restantes < 7: cor, label = "#ef4444", "Acabando"
            elif dias_restantes < 15: cor, label = "#f59e0b", "Atenção"
            else: cor, label = "#10b981", "Estoque Ok"

            # Layout do Card "Lego" (Fácil de entender)
            st.markdown(f"""
                <div class="med-card">
                    <div class="card-header">
                        <span style="font-size: 1.4rem; font-weight: 800;">{r['nome'].upper()}</span>
                        <span class="status-badge" style="background-color: {cor};">{label}</span>
                    </div>
                    <div class="price-tag">💲 Último Preço: R$ {r['preco']:.2f}</div>
                    <div class="stock-box">
                        <div class="stock-item">
                            <span class="stock-value">{estoque_atual}</span>
                            <span class="stock-label">Disponíveis</span>
                        </div>
                        <div class="stock-item" style="border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0;">
                            <span class="stock-value">{dias_restantes}</span>
                            <span class="stock-label">Dias Restantes</span>
                        </div>
                        <div class="stock-item">
                            <span class="stock-value" style="font-size: 1.1rem; padding-top: 5px;">{data_fim.strftime('%d/%b')}</span>
                            <span class="stock-label">Data Limite</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if st.session_state.admin:
                with st.expander(f"➕ Reposição e Preço para {r['nome']}"):
                    c1, c2 = st.columns(2)
                    n_q = c1.number_input("Quanto comprou?", 1, 500, 30, key=f"q_{r['id']}")
                    # FUNCIONALIDADE VOLTOU: Ajuste de preço na reposição
                    n_v = c2.number_input("Novo Preço R$", 0.0, 5000.0, float(r['preco']), key=f"v_{r['id']}")
                    
                    if st.button(f"Atualizar {r['nome']}", key=f"btn_{r['id']}"):
                        nova_qtd = estoque_atual + n_q
                        requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={
                            "qtd_total": int(nova_qtd), 
                            "data_inicio": str(hoje.date()),
                            "preco": float(n_v)
                        })
                        requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={
                            "nome_remedio": r['nome'], 
                            "valor": float(n_v), 
                            "data_compra": str(hoje.date())
                        })
                        enviar_telegram(f"📦 Reposição: {r['nome']}\nQtd: +{n_q} | Novo Preço: R${n_v}")
                        st.success("Estoque e Preço Atualizados!"); time.sleep(1); st.rerun()

elif menu == "⚙️ Cadastros":
    st.title("➕ Novos Registros")
    if not st.session_state.admin: st.warning("Área de Administrador.")
    else:
        opcao = st.radio("Selecione o tipo", ["Remédio", "Consulta"], horizontal=True)
        with st.container(border=True):
            if opcao == "Remédio":
                n = st.text_input("Nome do Remédio")
                c1, c2, c3 = st.columns(3)
                q = c1.number_input("Qtd Caixa", 1)
                d = c2.number_input("Dose/Dia", 0.1, 10.0, 1.0)
                p = c3.number_input("Preço R$", 0.0)
                if st.button("Cadastrar Remédio"):
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":n,"valor":float(p),"data_compra":str(datetime.now().date())})
                    st.success("Sucesso!"); time.sleep(1); st.rerun()
            else:
                m = st.text_input("Médico")
                v = st.number_input("Valor R$", 0.0)
                if st.button("Cadastrar Consulta"):
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":m, "valor":float(v), "data_consulta":str(datetime.now().date())})
                    st.success("Sucesso!"); time.sleep(1); st.rerun()

elif menu == "💰 Gastos Detalhados":
    st.title("💰 Controle Financeiro")
    df_r, df_c = api_get("compras"), api_get("consultas")
    t1 = df_r['valor'].sum() if not df_r.empty else 0
    t2 = df_c['valor'].sum() if not df_c.empty else 0
    
    col1, col2 = st.columns(2)
    col1.metric("Gasto com Remédios", f"R$ {t1:.2f}")
    col2.metric("Gasto com Consultas", f"R$ {t2:.2f}")
    st.subheader(f"Total Geral: R$ {t1+t2:.2f}")
    
    with st.expander("Ver histórico de compras"):
        if not df_r.empty: st.dataframe(df_r[['data_compra', 'nome_remedio', 'valor']], use_container_width=True)

elif menu == "🗑️ Apagar":
    st.title("🗑️ Remover Dados")
    if not st.session_state.admin: st.error("Acesso Negado.")
    else:
        cat = st.selectbox("Categoria", ["remedios", "consultas", "compras"])
        df_d = api_get(cat)
        if not df_d.empty:
            ref = 'nome' if cat == 'remedios' else 'medico' if cat == 'consultas' else 'nome_remedio'
            item = st.selectbox("Item", df_d[ref].tolist())
            if st.button("Confirmar Exclusão"):
                id_i = df_d[df_d[ref] == item]['id'].values[0]
                requests.delete(f"{URL_SUPABASE}{cat}?id=eq.{id_i}", headers=HEADERS)
                st.rerun()

elif menu == "🩺 Minhas Consultas":
    st.title("🩺 Histórico Médico")
    df_c = api_get("consultas")
    if df_c.empty: st.info("Sem consultas.")
    else:
        for _, c in df_c.iterrows():
            st.markdown(f"""
                <div class="med-card" style="border-left: 8px solid #3b82f6;">
                    <div class="card-header">
                        <span style="font-size: 1.2rem;">{c['medico']}</span>
                        <span style="color: #64748b;">{c['data_consulta'].strftime('%d/%m/%Y')}</span>
                    </div>
                    <b style="color: #059669;">Investimento: R$ {c['valor']:.2f}</b>
                </div>
            """, unsafe_allow_html=True)
