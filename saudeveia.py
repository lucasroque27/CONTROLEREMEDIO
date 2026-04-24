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

HEADERS = {"apikey": API_KEY, "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}

def enviar_telegram(mensagem):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", data={"chat_id": CHAT_ID, "text": mensagem}, timeout=5)
    except: pass

def api_get(tabela):
    try:
        res = requests.get(f"{URL_SUPABASE}{tabela}?select=*&order=id.desc", headers=HEADERS)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            for col in ['data_inicio', 'data_consulta', 'data_compra']:
                if not df.empty and col in df.columns: df[col] = pd.to_datetime(df[col])
            return df
    except: pass
    return pd.DataFrame()

# --- 2. ESTILO ORIGINAL RESGATADO E CORRIGIDO ---
st.set_page_config(page_title="Controle de Medicamentos", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    /* Fundo da tela mais limpo */
    .stApp { background-color: #f4f6f9; }
    
    /* CORREÇÃO DO MENU: Mantém o header transparente para o botão do celular aparecer */
    header { background-color: transparent !important; }
    .block-container { padding-top: 2rem !important; }
    
    /* O visual perfeito do Card */
    .card-remedio {
        background-color: white;
        border-radius: 12px;
        padding: 20px 25px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        margin-bottom: 5px;
        margin-top: 15px;
        border: 1px solid #eef0f5;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 5px;
    }
    .remedio-title {
        font-size: 20px;
        font-weight: 800;
        color: #2c3e50;
        margin: 0;
        text-transform: uppercase;
    }
    /* Estilos das Pílulas de Status */
    .badge-ok { background-color: #1dd1a1; color: white; padding: 5px 15px; border-radius: 20px; font-size: 11px; font-weight: bold; letter-spacing: 0.5px;}
    .badge-alerta { background-color: #feca57; color: #2c3e50; padding: 5px 15px; border-radius: 20px; font-size: 11px; font-weight: bold; letter-spacing: 0.5px;}
    .badge-repor { background-color: #ff6b6b; color: white; padding: 5px 15px; border-radius: 20px; font-size: 11px; font-weight: bold; letter-spacing: 0.5px;}
    
    .preco { color: #10ac84; font-size: 13px; font-weight: 600; margin-bottom: 20px; }
    
    .grid-stats {
        display: flex;
        justify-content: space-between;
        text-align: center;
        border-top: 1px solid #f1f2f6;
        padding-top: 15px;
    }
    .stat-box { flex: 1; }
    .stat-box:not(:last-child) { border-right: 1px solid #f1f2f6; }
    .stat-num { font-size: 18px; font-weight: 800; color: #2c3e50; margin: 0; }
    .stat-label { font-size: 11px; color: #7f8c8d; margin: 0; margin-top: 4px; }
    
    /* Ajuste fino do expander para colar embaixo do card */
    div[data-testid="stExpander"] { border-radius: 8px !important; margin-bottom: 15px; background-color: #fcfcfc;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÓGICA DE ALERTAS ---
if "notificou_entrada" not in st.session_state:
    enviar_telegram("🔌 App acessado: Verificação de medicamentos iniciada.")
    st.session_state.notificou_entrada = True

# --- 4. MENU LATERAL ---
with st.sidebar:
    st.title("💊 Gestão")
    if "admin" not in st.session_state: st.session_state.admin = False
    
    if not st.session_state.admin:
        pw = st.text_input("Senha", type="password")
        if st.button("Acessar"):
            if pw == "1234": st.session_state.admin = True; st.rerun()
    else:
        if st.button("Sair"): st.session_state.admin = False; st.rerun()

    aba = st.radio("Menu", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"], label_visibility="collapsed")

meses_pt = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}

# --- 5. TELA DE ESTOQUE (VISUAL AJUSTADO) ---
if aba == "Estoque":
    st.markdown("<h2>💊 Controle de Medicamentos</h2>", unsafe_allow_html=True)
    df = api_get("remedios")
    
    if not df.empty:
        hoje = datetime.now()
        itens_criticos = []

        for _, r in df.iterrows():
            dias_p = (hoje - r['data_inicio']).days
            estoque = max(0, int(r['qtd_total'] - (dias_p * r['dose_diaria'])))
            dias_r = int(estoque / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_f = hoje + timedelta(days=dias_r)
            
            if dias_r < 7:
                classe_badge = "badge-repor"
                texto_badge = "REPOR ESTOQUE"
                itens_criticos.append(f"🚨 {r['nome'].upper()} ({dias_r} dias rest.)")
            elif dias_r < 15:
                classe_badge = "badge-alerta"
                texto_badge = "ATENÇÃO"
            else:
                classe_badge = "badge-ok"
                texto_badge = "ESTOQUE OK"

            # Card com a Dose Diária adicionada!
            card_html = f"""
            <div class="card-remedio">
                <div class="card-header">
                    <p class="remedio-title">{r['nome']}</p>
                    <span class="{classe_badge}">{texto_badge}</span>
                </div>
                <div class="preco">$ Último Preço: R$ {r['preco']:.2f}</div>
                <div class="grid-stats">
                    <div class="stat-box">
                        <p class="stat-num">{estoque}</p>
                        <p class="stat-label">Disponíveis</p>
                    </div>
                    <div class="stat-box">
                        <p class="stat-num">{r['dose_diaria']}</p>
                        <p class="stat-label">Por Dia</p>
                    </div>
                    <div class="stat-box">
                        <p class="stat-num">{dias_r}</p>
                        <p class="stat-label">Dias Restantes</p>
                    </div>
                    <div class="stat-box">
                        <p class="stat-num">{data_f.day}/{meses_pt[data_f.month]}</p>
                        <p class="stat-label">Data Limite</p>
                    </div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

            if st.session_state.admin:
                with st.expander(f"➕ Reposição e Preço para {r['nome']}"):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    nq = c1.number_input("Adicionar Qtd", 1, 500, 30, key=f"q_{r['id']}")
                    np = c2.number_input("Novo Preço R$", 0.0, 5000.0, float(r['preco']), key=f"p_{r['id']}")
                    
                    c3.markdown("<br>", unsafe_allow_html=True)
                    if c3.button("Salvar", key=f"b_{r['id']}", use_container_width=True):
                        requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": int(estoque + nq), "data_inicio": str(hoje.date()), "preco": float(np)})
                        requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": float(np), "data_compra": str(hoje.date())})
                        
                        enviar_telegram(f"✅ Reposição Efetuada!\n💊 {r['nome']}\n📦 Novo total: {int(estoque + nq)} un.")
                        st.rerun()

        if itens_criticos and "notificou_estoque" not in st.session_state:
            enviar_telegram("⚠️ **ESTOQUE BAIXO!**\n" + "\n".join(itens_criticos))
            st.session_state.notificou_estoque = True

# --- 6. OUTRAS TELAS ---
elif aba == "Financeiro":
    st.markdown("<h2>💰 Gastos</h2>", unsafe_allow_html=True)
    df_f = api_get("compras")
    if not df_f.empty:
        st.metric("Total Acumulado", f"R$ {df_f['valor'].sum():.2f}")
        st.dataframe(df_f[['data_compra', 'nome_remedio', 'valor']], use_container_width=True, hide_index=True)

elif aba == "Consultas":
    st.markdown("<h2>🩺 Consultas</h2>", unsafe_allow_html=True)
    df_c = api_get("consultas")
    if not df_c.empty:
        for _, c in df_c.iterrows():
            with st.container(border=True):
                st.write(f"**{c['medico']}** | R$ {c['valor']:.2f} | {c['data_consulta'].strftime('%d/%m/%Y')}")

elif aba == "Cadastrar":
    st.markdown("<h2>➕ Novo Medicamento</h2>", unsafe_allow_html=True)
    if st.session_state.admin:
        with st.form("cad"):
            nome = st.text_input("Nome")
            c1, c2, c3 = st.columns(3)
            qtd = c1.number_input("Qtd Inicial", 1)
            dose = c2.number_input("Dose Diária", 0.1, 10.0, 1.0)
            preco = c3.number_input("Preço", 0.0)
            if st.form_submit_button("Salvar no Sistema"):
                requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":nome,"qtd_total":int(qtd),"dose_diaria":float(dose),"preco":float(preco),"data_inicio":str(datetime.now().date())})
                requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":nome,"valor":float(preco),"data_compra":str(datetime.now().date())})
                enviar_telegram(f"🆕 Novo cadastro: {nome}")
                st.rerun()

elif aba == "Remover":
    st.markdown("<h2>🗑️ Remover</h2>", unsafe_allow_html=True)
    if st.session_state.admin:
        df_d = api_get("remedios")
        if not df_d.empty:
            it = st.selectbox("Escolha o medicamento", df_d['nome'].tolist())
            if st.button("Confirmar Exclusão", type="primary"):
                id_item = df_d[df_d['nome'] == it]['id'].values[0]
                requests.delete(f"{URL_SUPABASE}remedios?id=eq.{id_item}", headers=HEADERS)
                st.rerun()
