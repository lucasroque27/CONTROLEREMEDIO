import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

# --- 1. CONFIGURAÇÕES (Pilar: Conectividade) ---
URL_SUPABASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
TOKEN_TELEGRAM = "8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM"
CHAT_ID = "5256921022"

HEADERS = {"apikey": API_KEY, "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}

# Pilar: Comunicação (Telegram)
def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}, timeout=3)
    except: pass 

@st.cache_data(ttl=300)
def api_get(tabela):
    try:
        res = requests.get(f"{URL_SUPABASE}{tabela}?select=*&order=id.desc", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            for col in ['data_inicio', 'data_consulta', 'data_compra']:
                if not df.empty and col in df.columns: df[col] = pd.to_datetime(df[col])
            return df
    except: pass
    return pd.DataFrame()

# --- 2. ESTILO VISUAL ---
st.set_page_config(page_title="Gestão de Saúde", page_icon="💊", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .card-remedio {
        background-color: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-top: 15px; border: 1px solid #eef2f7;
    }
    .remedio-title { font-size: 18px; font-weight: 800; color: #2c3e50; text-transform: uppercase; }
    .stat-num { font-size: 20px; font-weight: 800; color: #2c3e50; }
    .stat-label { font-size: 12px; color: #7f8c8d; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN (Pilar: Acesso - Enter + Botão) ---
if "admin" not in st.session_state: st.session_state.admin = False

with st.sidebar:
    st.title("🛡️ Gestão")
    if not st.session_state.admin:
        pw = st.text_input("Senha Administrativa", type="password", key="login_pw")
        # Valida ao clicar ou ao dar Enter (quando o valor de pw coincide)
        if st.button("Acessar Painel", use_container_width=True) or (pw == "1234"):
            if pw == "1234":
                st.session_state.admin = True
                st.rerun()
            elif pw != "":
                st.error("Senha incorreta!")
    else:
        st.success("Modo ADM Ativo")
        if st.button("Sair do Modo ADM", use_container_width=True):
            st.session_state.admin = False
            st.rerun()
    
    aba = st.radio("Navegação:", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"], key="nav_id")

# --- 4. TELAS ---

if aba == "Estoque":
    st.markdown("<h2>📋 Resumo de Medicamentos</h2>", unsafe_allow_html=True)
    df = api_get("remedios")
    if not df.empty:
        hoje = datetime.now()
        criticos = []
        for _, r in df.iterrows():
            # Pilar: Lógica de Estoque
            dias_p = (hoje - r['data_inicio']).days
            estoque = max(0, int(r['qtd_total'] - (dias_p * r['dose_diaria'])))
            dias_r = int(estoque / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_f = hoje + timedelta(days=dias_r)
            
            if dias_r < 7: criticos.append(f"🔴 {r['nome']} ({dias_r} dias)")

            st.markdown(f"""
            <div class="card-remedio">
                <p class="remedio-title">💊 {r['nome']}</p>
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div><p class="stat-num">{estoque}</p><p class="stat-label">Qtd</p></div>
                    <div><p class="stat-num">{r['dose_diaria']}</p><p class="stat-label">Dose/Dia</p></div>
                    <div><p class="stat-num">{dias_r}d</p><p class="stat-label">Restam</p></div>
                    <div><p class="stat-num">{data_f.strftime('%d/%m')}</p><p class="stat-label">Fim</p></div>
                </div>
            </div>""", unsafe_allow_html=True)

            if st.session_state.admin:
                with st.expander(f"Ajustar {r['nome']}"):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    nq = c1.number_input("+ Adicionar Qtd", 1, 500, 30, key=f"q_{r['id']}")
                    np = c2.number_input("Novo Preço R$", 0.0, 5000.0, float(r['preco']), key=f"p_{r['id']}")
                    if c3.button("Salvar", key=f"btn_{r['id']}", use_container_width=True):
                        requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(estoque + nq), "data_inicio": str(hoje.date()), "preco": float(np)})
                        requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(np), "data_compra": str(hoje.date())})
                        st.cache_data.clear()
                        enviar_telegram(f"✅ Reposição de {r['nome']} realizada.")
                        st.rerun()
        
        if criticos and "aviso_enviado" not in st.session_state:
            enviar_telegram("⚠️ **ATENÇÃO:** Estoque acabando:\n" + "\n".join(criticos))
            st.session_state.aviso_enviado = True

elif aba == "Financeiro":
    st.markdown("<h2>📊 Análise Financeira</h2>", unsafe_allow_html=True)
    df_r, df_c = api_get("compras"), api_get("consultas")
    
    # Pilar: Evolução Gráfica (Corrigida e Legível)
    fin_data = []
    if not df_r.empty:
        df_r_tmp = df_r[['data_compra', 'valor']].rename(columns={'data_compra': 'Data'})
        df_r_tmp['Categoria'] = 'Remédios'
        fin_data.append(df_r_tmp)
    if not df_c.empty:
        df_c_tmp = df_c[['data_consulta', 'valor']].rename(columns={'data_consulta': 'Data'})
        df_c_tmp['Categoria'] = 'Consultas'
        fin_data.append(df_c_tmp)
    
    if fin_data:
        df_total = pd.concat(fin_data).sort_values('Data')
        df_total['Mês'] = df_total['Data'].dt.strftime('%m/%Y')
        
        # Agrupa por Mês e Categoria para evitar o "blocão" azul
        df_grouped = df_total.groupby(['Mês', 'Categoria'])['valor'].sum().reset_index()
        
        st.subheader("Gastos Mensais por Tipo (R$)")
        st.bar_chart(df_grouped, x="Mês", y="valor", color="Categoria", use_container_width=True)
        
        c1, c2 = st.columns(2)
        c1.metric("Total Remédios", f"R$ {df_r['valor'].sum() if not df_r.empty else 0:.2f}")
        c2.metric("Total Consultas", f"R$ {df_c['valor'].sum() if not df_c.empty else 0:.2f}")
    else:
        st.info("Sem dados financeiros.")

elif aba == "Consultas":
    st.markdown("<h2>🩺 Consultas Agendadas</h2>", unsafe_allow_html=True)
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            st.info(f"📅 {c['data_consulta'].strftime('%d/%m/%Y')} - {c['medico']} (R$ {c['valor']:.2f})")

elif aba == "Cadastrar":
    if st.session_state.admin:
        tipo = st.selectbox("O que cadastrar?", ["Remédio", "Consulta"])
        with st.form("f_novo"):
            if tipo == "Remédio":
                n, q, d, p = st.text_input("Nome"), st.number_input("Qtd", 1), st.number_input("Dose/Dia", 1.0), st.number_input("Preço", 0.0)
                if st.form_submit_button("Salvar"):
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    st.cache_data.clear(); enviar_telegram(f"🆕 Novo remédio: {n}"); st.rerun()
            else:
                m, v, dt = st.text_input("Médico"), st.number_input("Valor"), st.date_input("Data")
                if st.form_submit_button("Salvar"):
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    st.cache_data.clear(); st.rerun()
    else: st.warning("Acesso exclusivo ADM.")

elif aba == "Remover":
    if st.session_state.admin:
        op = st.radio("Remover de:", ["Remédio", "Consulta"])
        df_rem = api_get("remedios" if op == "Remédio" else "consultas")
        if not df_rem.empty:
            item = st.selectbox("Selecione:", df_rem['nome' if op == "Remédio" else 'medico'].tolist())
            if st.button("🗑️ Excluir", type="primary", use_container_width=True):
                id_rem = df_rem[df_rem['nome' if op == "Remédio" else 'medico'] == item]['id'].values[0]
                requests.delete(f"{URL_SUPABASE}{'remedios' if op == 'Remédio' else 'consultas'}?id=eq.{id_rem}", headers=HEADERS)
                st.cache_data.clear(); st.rerun()
    else: st.warning("Acesso exclusivo ADM.")
