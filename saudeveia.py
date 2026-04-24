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

# FUNÇÃO DE TELEGRAM PROTEGIDA CONTRA QUEDAS
def enviar_telegram(mensagem):import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

# --- 1. CONFIGURAÇÕES ---
URL_SUPABASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
TOKEN_TELEGRAM = "8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM"
CHAT_ID = "5256921022"

HEADERS = {"apikey": API_KEY, "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}

# FUNÇÃO DE TELEGRAM PROTEGIDA CONTRA QUEDAS
def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        # Timeout curto para não travar o app se o Telegram demorar
        requests.post(url, json={"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}, timeout=3)
    except:
        pass 

# CACHE DE DADOS PARA ESTABILIDADE (Evita sair do ar)
@st.cache_data(ttl=300)
def api_get(tabela):
    try:
        res = requests.get(f"{URL_SUPABASE}{tabela}?select=*&order=id.desc", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            for col in ['data_inicio', 'data_consulta', 'data_compra']:
                if not df.empty and col in df.columns: df[col] = pd.to_datetime(df[col])
            return df
    except:
        pass
    return pd.DataFrame()

# --- 2. ESTILO VISUAL (COMPLETO) ---
st.set_page_config(page_title="Gestão de Saúde", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f4f6f9; }
    /* Header transparente para não esconder o menu no celular */
    header { background-color: transparent !important; }
    .block-container { padding-top: 1.5rem !important; }
    .card-remedio {
        background-color: white; border-radius: 12px; padding: 20px 25px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02); margin-bottom: 5px;
        margin-top: 15px; border: 1px solid #eef0f5; font-family: 'Segoe UI', sans-serif;
    }
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
    .remedio-title { font-size: 20px; font-weight: 800; color: #2c3e50; margin: 0; text-transform: uppercase; }
    .badge-ok { background-color: #1dd1a1; color: white; padding: 5px 15px; border-radius: 20px; font-size: 11px; font-weight: bold; }
    .badge-alerta { background-color: #feca57; color: #2c3e50; padding: 5px 15px; border-radius: 20px; font-size: 11px; font-weight: bold; }
    .badge-repor { background-color: #ff6b6b; color: white; padding: 5px 15px; border-radius: 20px; font-size: 11px; font-weight: bold; }
    .preco { color: #10ac84; font-size: 13px; font-weight: 600; margin-bottom: 20px; }
    .grid-stats { display: flex; justify-content: space-between; text-align: center; border-top: 1px solid #f1f2f6; padding-top: 15px; }
    .stat-box { flex: 1; }
    .stat-box:not(:last-child) { border-right: 1px solid #f1f2f6; }
    .stat-num { font-size: 18px; font-weight: 800; color: #2c3e50; margin: 0; }
    .stat-label { font-size: 11px; color: #7f8c8d; margin: 0; margin-top: 4px; }
    div[data-testid="stExpander"] { border-radius: 8px !important; margin-bottom: 15px; background-color: #fcfcfc;}
    </style>
    """, unsafe_allow_html=True)

# ALERTA: APP ACESSADO
if "first_run" not in st.session_state:
    enviar_telegram("🚀 **Sistema Online:** O painel de saúde foi acessado.")
    st.session_state.first_run = True

# --- 3. MENU LATERAL COM BOTÕES PARA MOBILE ---
with st.sidebar:
    st.title("🛡️ Painel")
    if "admin" not in st.session_state: st.session_state.admin = False
    
    if not st.session_state.admin:
        pw = st.text_input("Senha ADM", type="password")
        if st.button("Acessar", use_container_width=True):
            if pw == "1234":
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
    else:
        if st.button("Sair", use_container_width=True): 
            st.session_state.admin = False
            st.rerun()
            
    aba = st.radio("Navegação", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"], label_visibility="collapsed")

meses_pt = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}

# --- 4. TELA DE ESTOQUE ---
if aba == "Estoque":
    st.markdown("<h2>💊 Meus Medicamentos</h2>", unsafe_allow_html=True)
    df = api_get("remedios")
    
    if not df.empty:
        hoje = datetime.now()
        itens_criticos = []

        for _, r in df.iterrows():
            dias_p = (hoje - r['data_inicio']).days
            estoque = max(0, int(r['qtd_total'] - (dias_p * r['dose_diaria'])))
            dias_r = int(estoque / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_f = hoje + timedelta(days=dias_r)
            
            # Controle Visual da Pílula (Badge)
            badge = "badge-ok" if dias_r >= 15 else ("badge-alerta" if dias_r >= 7 else "badge-repor")
            txt_badge = "ESTOQUE OK" if dias_r >= 15 else ("ATENÇÃO" if dias_r >= 7 else "REPOR")

            # Separando os itens críticos para enviar no Telegram
            if dias_r < 7:
                itens_criticos.append(f"🔴 {r['nome']} ({dias_r} dias restantes)")

            # Visual do Cartão
            st.markdown(f"""
            <div class="card-remedio">
                <div class="card-header"><p class="remedio-title">{r['nome']}</p><span class="{badge}">{txt_badge}</span></div>
                <div class="preco">$ Última Compra: R$ {r['preco']:.2f}</div>
                <div class="grid-stats">
                    <div class="stat-box"><p class="stat-num">{estoque}</p><p class="stat-label">Disponível</p></div>
                    <div class="stat-box"><p class="stat-num">{r['dose_diaria']}</p><p class="stat-label">Por Dia</p></div>
                    <div class="stat-box"><p class="stat-num">{dias_r}d</p><p class="stat-label">Duração</p></div>
                    <div class="stat-box"><p class="stat-num">{data_f.day}/{meses_pt[data_f.month]}</p><p class="stat-label">Fim Em</p></div>
                </div>
            </div>""", unsafe_allow_html=True)
            
            # Opção de Reposição
            if st.session_state.admin:
                with st.expander(f"➕ Ajustar {r['nome']}"):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    nq = c1.number_input("+ Qtd", 1, 500, 30, key=f"q_{r['id']}")
                    np = c2.number_input("Preço R$", 0.0, 5000.0, float(r['preco']), key=f"p_{r['id']}")
                    
                    c3.markdown("<br>", unsafe_allow_html=True)
                    if c3.button("Salvar", key=f"b_{r['id']}", use_container_width=True):
                        # Salva no banco de dados
                        requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(estoque + nq), "data_inicio": str(hoje.date()), "preco": float(np)})
                        requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(np), "data_compra": str(hoje.date())})
                        
                        # Limpa memória e avisa no Telegram
                        st.cache_data.clear()
                        enviar_telegram(f"✅ **Reposição Efetuada:**\n💊 Remédio: {r['nome']}\n📦 Novo total: {int(estoque + nq)} unidades.")
                        st.rerun()

        # ALERTA: ESTOQUE CRÍTICO
        if itens_criticos and "aviso_enviado" not in st.session_state:
            mensagem = "⚠️ **ATENÇÃO - ESTOQUE BAIXO:**\n" + "\n".join(itens_criticos)
            enviar_telegram(mensagem)
            st.session_state.aviso_enviado = True

# --- 5. TELA FINANCEIRA ---
elif aba == "Financeiro":
    st.markdown("<h2>💰 Controle de Gastos</h2>", unsafe_allow_html=True)
    df_r, df_c = api_get("compras"), api_get("consultas")
    
    t_r = df_r['valor'].sum() if not df_r.empty else 0
    t_c = df_c['valor'].sum() if not df_c.empty else 0
    
    col1, col2 = st.columns(2)
    col1.metric("💊 Remédios", f"R$ {t_r:.2f}")
    col2.metric("🩺 Consultas", f"R$ {t_c:.2f}")
    st.success(f"**Gasto Geral Acumulado: R$ {t_r + t_c:.2f}**")
    
    with st.expander("Ver Histórico de Remédios"):
        if not df_r.empty: st.dataframe(df_r[['data_compra', 'nome_remedio', 'valor']], use_container_width=True, hide_index=True)
    with st.expander("Ver Histórico de Consultas"):
        if not df_c.empty: st.dataframe(df_c[['data_consulta', 'medico', 'valor']], use_container_width=True, hide_index=True)

# --- 6. TELA DE CONSULTAS ---
elif aba == "Consultas":
    st.markdown("<h2>🩺 Consultas Agendadas</h2>", unsafe_allow_html=True)
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            with st.container(border=True):
                st.write(f"👨‍⚕️ **Médico/Especialidade:** {c['medico']}")
                st.write(f"📅 {c['data_consulta'].strftime('%d/%m/%Y')} | 💰 Valor: R$ {c['valor']:.2f}")

# --- 7. TELA DE CADASTRO ---
elif aba == "Cadastrar":
    st.markdown("<h2>➕ Adicionar Novo</h2>", unsafe_allow_html=True)
    if st.session_state.admin:
        tipo = st.selectbox("O que deseja cadastrar?", ["Remédio", "Consulta"])
        with st.form("form_cad"):
            if tipo == "Remédio":
                n = st.text_input("Nome do Medicamento")
                q = st.number_input("Quantidade Inicial", 1)
                d = st.number_input("Dose Diária", 0.1, 10.0, 1.0)
                p = st.number_input("Preço de Compra", 0.0)
                if st.form_submit_button("Salvar Remédio"):
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    st.cache_data.clear()
                    enviar_telegram(f"🆕 **Novo Cadastro:** Medicamento '{n}' adicionado ao sistema.")
                    st.rerun()
            else:
                m = st.text_input("Médico ou Especialidade")
                v = st.number_input("Valor da Consulta", 0.0)
                dt = st.date_input("Data da Consulta")
                if st.form_submit_button("Salvar Consulta"):
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    st.cache_data.clear()
                    enviar_telegram(f"🩺 **Nova Consulta Agendada:** {m} para o dia {dt.strftime('%d/%m/%Y')}.")
                    st.rerun()
    else:
        st.warning("Faça login como Administrador para cadastrar.")

# --- 8. TELA DE REMOÇÃO ---
elif aba == "Remover":
    st.markdown("<h2>🗑️ Apagar Registros</h2>", unsafe_allow_html=True)
    if st.session_state.admin:
        opcao = st.radio("O que deseja remover?", ["Remédio", "Consulta"])
        if opcao == "Remédio":
            df_d = api_get("remedios")
            if not df_d.empty:
                it = st.selectbox("Selecione o Remédio para excluir", df_d['nome'].tolist())
                if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
                    id_i = df_d[df_d['nome'] == it]['id'].values[0]
                    requests.delete(f"{URL_SUPABASE}remedios?id=eq.{id_i}", headers=HEADERS)
                    st.cache_data.clear()
                    st.rerun()
        else:
            df_dc = api_get("consultas")
            if not df_dc.empty:
                lista_c = [f"{c['medico']} ({c['data_consulta'].strftime('%d/%m')})" for _, c in df_dc.iterrows()]
                it_c = st.selectbox("Selecione a Consulta para excluir", lista_c)
                if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
                    idx = lista_c.index(it_c)
                    id_c = df_dc.iloc[idx]['id']
                    requests.delete(f"{URL_SUPABASE}consultas?id=eq.{id_c}", headers=HEADERS)
                    st.cache_data.clear()
                    st.rerun()
    else:
        st.warning("Faça login como Administrador para remover itens.")
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        # Timeout de 3 segundos: se o Telegram demorar, o app ignora e segue rodando para não travar sua tela
        requests.post(url, json={"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}, timeout=3)
    except:
        pass 

# CACHE DE DADOS PARA ESTABILIDADE (Evita sair do ar)
@st.cache_data(ttl=300)
def api_get(tabela):
    try:
        res = requests.get(f"{URL_SUPABASE}{tabela}?select=*&order=id.desc", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            for col in ['data_inicio', 'data_consulta', 'data_compra']:
                if not df.empty and col in df.columns: df[col] = pd.to_datetime(df[col])
            return df
    except:
        pass
    return pd.DataFrame()

# --- 2. ESTILO VISUAL (COMPLETO) ---
st.set_page_config(page_title="Gestão de Saúde", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f4f6f9; }
    /* Header transparente para não esconder o menu no celular */
    header { background-color: transparent !important; }
    .block-container { padding-top: 1.5rem !important; }
    .card-remedio {
        background-color: white; border-radius: 12px; padding: 20px 25px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02); margin-bottom: 5px;
        margin-top: 15px; border: 1px solid #eef0f5; font-family: 'Segoe UI', sans-serif;
    }
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
    .remedio-title { font-size: 20px; font-weight: 800; color: #2c3e50; margin: 0; text-transform: uppercase; }
    .badge-ok { background-color: #1dd1a1; color: white; padding: 5px 15px; border-radius: 20px; font-size: 11px; font-weight: bold; }
    .badge-alerta { background-color: #feca57; color: #2c3e50; padding: 5px 15px; border-radius: 20px; font-size: 11px; font-weight: bold; }
    .badge-repor { background-color: #ff6b6b; color: white; padding: 5px 15px; border-radius: 20px; font-size: 11px; font-weight: bold; }
    .preco { color: #10ac84; font-size: 13px; font-weight: 600; margin-bottom: 20px; }
    .grid-stats { display: flex; justify-content: space-between; text-align: center; border-top: 1px solid #f1f2f6; padding-top: 15px; }
    .stat-box { flex: 1; }
    .stat-box:not(:last-child) { border-right: 1px solid #f1f2f6; }
    .stat-num { font-size: 18px; font-weight: 800; color: #2c3e50; margin: 0; }
    .stat-label { font-size: 11px; color: #7f8c8d; margin: 0; margin-top: 4px; }
    div[data-testid="stExpander"] { border-radius: 8px !important; margin-bottom: 15px; background-color: #fcfcfc;}
    </style>
    """, unsafe_allow_html=True)

# ALERTA: APP ACESSADO
if "first_run" not in st.session_state:
    enviar_telegram("🚀 **Sistema Online:** O painel de saúde foi acessado.")
    st.session_state.first_run = True

# --- 3. MENU LATERAL ---
with st.sidebar:
    st.title("🛡️ Painel")
    if "admin" not in st.session_state: st.session_state.admin = False
    
    if not st.session_state.admin:
        if st.text_input("Senha ADM", type="password") == "1234":
            st.session_state.admin = True
            st.rerun()
    else:
        if st.button("Sair"): 
            st.session_state.admin = False
            st.rerun()
            
    aba = st.radio("Navegação", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"], label_visibility="collapsed")

meses_pt = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}

# --- 4. TELA DE ESTOQUE ---
if aba == "Estoque":
    st.markdown("<h2>💊 Meus Medicamentos</h2>", unsafe_allow_html=True)
    df = api_get("remedios")
    
    if not df.empty:
        hoje = datetime.now()
        itens_criticos = []

        for _, r in df.iterrows():
            dias_p = (hoje - r['data_inicio']).days
            estoque = max(0, int(r['qtd_total'] - (dias_p * r['dose_diaria'])))
            dias_r = int(estoque / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_f = hoje + timedelta(days=dias_r)
            
            # Controle Visual da Pílula (Badge)
            badge = "badge-ok" if dias_r >= 15 else ("badge-alerta" if dias_r >= 7 else "badge-repor")
            txt_badge = "ESTOQUE OK" if dias_r >= 15 else ("ATENÇÃO" if dias_r >= 7 else "REPOR")

            # Separando os itens críticos para enviar no Telegram
            if dias_r < 7:
                itens_criticos.append(f"🔴 {r['nome']} ({dias_r} dias restantes)")

            # Visual do Cartão
            st.markdown(f"""
            <div class="card-remedio">
                <div class="card-header"><p class="remedio-title">{r['nome']}</p><span class="{badge}">{txt_badge}</span></div>
                <div class="preco">$ Última Compra: R$ {r['preco']:.2f}</div>
                <div class="grid-stats">
                    <div class="stat-box"><p class="stat-num">{estoque}</p><p class="stat-label">Disponível</p></div>
                    <div class="stat-box"><p class="stat-num">{r['dose_diaria']}</p><p class="stat-label">Por Dia</p></div>
                    <div class="stat-box"><p class="stat-num">{dias_r}d</p><p class="stat-label">Duração</p></div>
                    <div class="stat-box"><p class="stat-num">{data_f.day}/{meses_pt[data_f.month]}</p><p class="stat-label">Fim Em</p></div>
                </div>
            </div>""", unsafe_allow_html=True)
            
            # Opção de Reposição
            if st.session_state.admin:
                with st.expander(f"➕ Ajustar {r['nome']}"):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    nq = c1.number_input("+ Qtd", 1, 500, 30, key=f"q_{r['id']}")
                    np = c2.number_input("Preço R$", 0.0, 5000.0, float(r['preco']), key=f"p_{r['id']}")
                    
                    c3.markdown("<br>", unsafe_allow_html=True)
                    if c3.button("Salvar", key=f"b_{r['id']}", use_container_width=True):
                        # Salva no banco de dados
                        requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(estoque + nq), "data_inicio": str(hoje.date()), "preco": float(np)})
                        requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(np), "data_compra": str(hoje.date())})
                        
                        # Limpa memória e avisa no Telegram
                        st.cache_data.clear()
                        enviar_telegram(f"✅ **Reposição Efetuada:**\n💊 Remédio: {r['nome']}\n📦 Novo total: {int(estoque + nq)} unidades.")
                        st.rerun()

        # ALERTA: ESTOQUE CRÍTICO
        if itens_criticos and "aviso_enviado" not in st.session_state:
            mensagem = "⚠️ **ATENÇÃO - ESTOQUE BAIXO:**\n" + "\n".join(itens_criticos)
            enviar_telegram(mensagem)
            st.session_state.aviso_enviado = True

# --- 5. TELA FINANCEIRA ---
elif aba == "Financeiro":
    st.markdown("<h2>💰 Controle de Gastos</h2>", unsafe_allow_html=True)
    df_r, df_c = api_get("compras"), api_get("consultas")
    
    t_r = df_r['valor'].sum() if not df_r.empty else 0
    t_c = df_c['valor'].sum() if not df_c.empty else 0
    
    col1, col2 = st.columns(2)
    col1.metric("💊 Remédios", f"R$ {t_r:.2f}")
    col2.metric("🩺 Consultas", f"R$ {t_c:.2f}")
    st.success(f"**Gasto Geral Acumulado: R$ {t_r + t_c:.2f}**")
    
    with st.expander("Ver Histórico de Remédios"):
        if not df_r.empty: st.dataframe(df_r[['data_compra', 'nome_remedio', 'valor']], use_container_width=True, hide_index=True)
    with st.expander("Ver Histórico de Consultas"):
        if not df_c.empty: st.dataframe(df_c[['data_consulta', 'medico', 'valor']], use_container_width=True, hide_index=True)

# --- 6. TELA DE CONSULTAS ---
elif aba == "Consultas":
    st.markdown("<h2>🩺 Consultas Agendadas</h2>", unsafe_allow_html=True)
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            with st.container(border=True):
                st.write(f"👨‍⚕️ **Médico/Especialidade:** {c['medico']}")
                st.write(f"📅 {c['data_consulta'].strftime('%d/%m/%Y')} | 💰 Valor: R$ {c['valor']:.2f}")

# --- 7. TELA DE CADASTRO ---
elif aba == "Cadastrar":
    st.markdown("<h2>➕ Adicionar Novo</h2>", unsafe_allow_html=True)
    if st.session_state.admin:
        tipo = st.selectbox("O que deseja cadastrar?", ["Remédio", "Consulta"])
        with st.form("form_cad"):
            if tipo == "Remédio":
                n = st.text_input("Nome do Medicamento")
                q = st.number_input("Quantidade Inicial", 1)
                d = st.number_input("Dose Diária", 0.1, 10.0, 1.0)
                p = st.number_input("Preço de Compra", 0.0)
                if st.form_submit_button("Salvar Remédio"):
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    st.cache_data.clear()
                    enviar_telegram(f"🆕 **Novo Cadastro:** Medicamento '{n}' adicionado ao sistema.")
                    st.rerun()
            else:
                m = st.text_input("Médico ou Especialidade")
                v = st.number_input("Valor da Consulta", 0.0)
                dt = st.date_input("Data da Consulta")
                if st.form_submit_button("Salvar Consulta"):
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":m, "valor":float(v), "data_consulta":str(dt)})
                    st.cache_data.clear()
                    enviar_telegram(f"🩺 **Nova Consulta Agendada:** {m} para o dia {dt.strftime('%d/%m/%Y')}.")
                    st.rerun()
    else:
        st.warning("Faça login como Administrador para cadastrar.")

# --- 8. TELA DE REMOÇÃO ---
elif aba == "Remover":
    st.markdown("<h2>🗑️ Apagar Registros</h2>", unsafe_allow_html=True)
    if st.session_state.admin:
        opcao = st.radio("O que deseja remover?", ["Remédio", "Consulta"])
        if opcao == "Remédio":
            df_d = api_get("remedios")
            if not df_d.empty:
                it = st.selectbox("Selecione o Remédio para excluir", df_d['nome'].tolist())
                if st.button("Confirmar Exclusão", type="primary"):
                    id_i = df_d[df_d['nome'] == it]['id'].values[0]
                    requests.delete(f"{URL_SUPABASE}remedios?id=eq.{id_i}", headers=HEADERS)
                    st.cache_data.clear()
                    st.rerun()
        else:
            df_dc = api_get("consultas")
            if not df_dc.empty:
                lista_c = [f"{c['medico']} ({c['data_consulta'].strftime('%d/%m')})" for _, c in df_dc.iterrows()]
                it_c = st.selectbox("Selecione a Consulta para excluir", lista_c)
                if st.button("Confirmar Exclusão", type="primary"):
                    idx = lista_c.index(it_c)
                    id_c = df_dc.iloc[idx]['id']
                    requests.delete(f"{URL_SUPABASE}consultas?id=eq.{id_c}", headers=HEADERS)
                    st.cache_data.clear()
                    st.rerun()
    else:
        st.warning("Faça login como Administrador para remover itens.")
