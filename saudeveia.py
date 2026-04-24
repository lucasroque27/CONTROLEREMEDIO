import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

# --- 1. CONFIGURAÇÕES ---
URL_SUPABASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
TOKEN_TELEGRAM = "8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM"
CHAT_ID = "5256921022"

HEADERS = {"apikey": API_KEY, "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}

# Função de alerta protegida
def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}, timeout=3)
    except:
        pass 

# Busca de dados com cache para não travar
@st.cache_data(ttl=300)
def api_get(tabela):
    try:
        res = requests.get(f"{URL_SUPABASE}{tabela}?select=*&order=id.desc", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            for col in ['data_inicio', 'data_consulta', 'data_compra']:
                if not df.empty and col in df.columns: 
                    df[col] = pd.to_datetime(df[col])
            return df
    except:
        pass
    return pd.DataFrame()

# --- 2. CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Gestão de Saúde", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f4f6f9; }
    .card-remedio {
        background-color: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02); margin-top: 15px; border: 1px solid #eef0f5;
    }
    .remedio-title { font-size: 18px; font-weight: 800; color: #2c3e50; text-transform: uppercase; margin-bottom: 10px; }
    .stat-num { font-size: 20px; font-weight: 800; color: #2c3e50; margin: 0; }
    .stat-label { font-size: 12px; color: #7f8c8d; margin: 0; }
    .badge-repor { background-color: #ff6b6b; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Aviso de Inicialização
if "first_run" not in st.session_state:
    enviar_telegram("🚀 **Sistema Online:** O painel de saúde foi acessado.")
    st.session_state.first_run = True

# --- 3. LOGIN (ENTER + BOTÃO + MOBILE OK) ---
if "admin" not in st.session_state: st.session_state.admin = False

with st.sidebar:
    st.title("🛡️ Painel de Gestão")
    if not st.session_state.admin:
        pw = st.text_input("Senha ADM", type="password", key="login_pw")
        # O sistema valida se o botão for clicado OU se a senha digitada for correta (Enter)
        if st.button("Acessar", use_container_width=True) or (pw == "1234"):
            if pw == "1234":
                st.session_state.admin = True
                st.rerun()
            elif pw != "":
                st.error("Senha incorreta!")
    else:
        st.success("Administrador logado")
        if st.button("Sair", use_container_width=True):
            st.session_state.admin = False
            st.rerun()
    
    aba = st.radio("Menu:", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"], key="nav_main")

meses_pt = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}

# --- 4. FUNCIONALIDADES ---

if aba == "Estoque":
    st.markdown("<h2>💊 Medicamentos</h2>", unsafe_allow_html=True)
    df = api_get("remedios")
    if not df.empty:
        hoje = datetime.now()
        itens_criticos = [] # Lista para o alerta do Telegram

        for _, r in df.iterrows():
            dias_p = (hoje - r['data_inicio']).days
            estoque = max(0, int(r['qtd_total'] - (dias_p * r['dose_diaria'])))
            dias_r = int(estoque / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_f = hoje + timedelta(days=dias_r)
            
            # Adiciona à lista de alerta se tiver menos de 7 dias
            if dias_r < 7:
                itens_criticos.append(f"🔴 {r['nome']} ({dias_r} dias)")

            st.markdown(f"""
            <div class="card-remedio">
                <p class="remedio-title">💊 {r['nome']}</p>
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div><p class="stat-num">{estoque}</p><p class="stat-label">Disponível</p></div>
                    <div><p class="stat-num">{r['dose_diaria']}</p><p class="stat-label">Dose/Dia</p></div>
                    <div><p class="stat-num">{dias_r}d</p><p class="stat-label">Duração</p></div>
                    <div><p class="stat-num">{data_f.day}/{meses_pt[data_f.month]}</p><p class="stat-label">Fim</p></div>
                </div>
            </div>""", unsafe_allow_html=True)

            if st.session_state.admin:
                with st.expander(f"Ajustar {r['nome']}"):
                    c1, c2, c3 = st.columns([2,2,1])
                    nq = c1.number_input("+ Adicionar", 1, 500, 30, key=f"q_{r['id']}")
                    np = c2.number_input("Preço R$", 0.0, 5000.0, float(r['preco']), key=f"p_{r['id']}")
                    if c3.button("Salvar", key=f"b_{r['id']}", use_container_width=True):
                        requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(estoque + nq), "data_inicio": str(hoje.date()), "preco": float(np)})
                        requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(np), "data_compra": str(hoje.date())})
                        st.cache_data.clear()
                        enviar_telegram(f"✅ **Reposição:** {r['nome']} agora tem {int(estoque + nq)} unidades.")
                        st.rerun()

        # Envia alerta de estoque baixo apenas uma vez por sessão
        if itens_criticos and "aviso_enviado" not in st.session_state:
            enviar_telegram("⚠️ **ALERTA DE ESTOQUE BAIXO:**\n" + "\n".join(itens_criticos))
            st.session_state.aviso_enviado = True

elif aba == "Financeiro":
    st.markdown("<h2>📊 Análise Financeira</h2>", unsafe_allow_html=True)
    df_r = api_get("compras")
    df_c = api_get("consultas")
    
    # Processamento para Gráficos
    dados = []
    if not df_r.empty:
        df_r_copy = df_r[['data_compra', 'valor']].rename(columns={'data_compra': 'data'})
        df_r_copy['Tipo'] = 'Remédio'
        dados.append(df_r_copy)
    if not df_c.empty:
        df_c_copy = df_c[['data_consulta', 'valor']].rename(columns={'data_consulta': 'data'})
        df_c_copy['Tipo'] = 'Consulta'
        dados.append(df_c_copy)
    
    if dados:
        df_total = pd.concat(dados)
        df_total['Mes/Ano'] = df_total['data'].dt.strftime('%m/%Y')
        
        # Gráfico de Gastos Mensais
        st.subheader("Gasto Mensal Total (R$)")
        chart_data = df_total.groupby('Mes/Ano')['valor'].sum().sort_index().reset_index()
        st.bar_chart(chart_data.set_index('Mes/Ano'))
        
        col1, col2 = st.columns(2)
        col1.metric("Total Remédios", f"R$ {df_r['valor'].sum() if not df_r.empty else 0:.2f}")
        col2.metric("Total Consultas", f"R$ {df_c['valor'].sum() if not df_c.empty else 0:.2f}")
    else:
        st.info("Aguardando registros para gerar gráficos.")

elif aba == "Consultas":
    st.markdown("<h2>🩺 Próximas Consultas</h2>", unsafe_allow_html=True)
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            st.info(f"👨‍⚕️ **{c['medico']}**\n📅 Data: {c['data_consulta'].strftime('%d/%m/%Y')} | Valor: R$ {c['valor']:.2f}")

elif aba == "Cadastrar":
    if st.session_state.admin:
        tipo = st.selectbox("O que deseja cadastrar?", ["Remédio", "Consulta"])
        with st.form("form_novo"):
            if tipo == "Remédio":
                n = st.text_input("Nome do Remédio")
                q = st.number_input("Quantidade Inicial", 1)
                d = st.number_input("Doses por Dia", 1.0)
                p = st.number_input("Preço", 0.0)
                if st.form_submit_button("Concluir Cadastro"):
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    st.cache_data.clear()
                    enviar_telegram(f"🆕 **Novo Cadastro:** {n} foi adicionado ao estoque.")
                    st.rerun()
            else:
                m = st.text_input("Médico/Especialidade")
                v = st.number_input("Valor", 0.0)
                dt = st.date_input("Data")
                if st.form_submit_button("Agendar"):
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    st.cache_data.clear()
                    enviar_telegram(f"🩺 **Nova Consulta:** {m} marcada para {dt.strftime('%d/%m/%Y')}.")
                    st.rerun()
    else:
        st.warning("Área restrita. Por favor, faça login no menu lateral.")

elif aba == "Remover":
    if st.session_state.admin:
        op = st.radio("Excluir de:", ["Remédio", "Consulta"])
        df_rem = api_get("remedios" if op == "Remédio" else "consultas")
        if not df_rem.empty:
            lista = df_rem['nome' if op == "Remédio" else 'medico'].tolist()
            item = st.selectbox("Selecione o item para apagar definitivamente:", lista)
            if st.button("🗑️ Remover Registro", type="primary", use_container_width=True):
                id_rem = df_rem[df_rem['nome' if op == "Remédio" else 'medico'] == item]['id'].values[0]
                requests.delete(f"{URL_SUPABASE}{'remedios' if op == 'Remédio' else 'consultas'}?id=eq.{id_rem}", headers=HEADERS)
                st.cache_data.clear()
                st.rerun()
    else:
        st.warning("Você precisa de acesso administrativo para remover dados.")
