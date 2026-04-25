import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

# --- 1. CONFIGURAÇÕES E PILARES (Estabilidade e Conectividade) ---
URL_BASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
HEADERS = {"apikey": API_KEY, "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "Prefer": "representation"}

def enviar_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM/sendMessage", 
                      json={"chat_id": "5256921022", "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

@st.cache_data(ttl=30) # Cache curto para manter os dados sempre frescos
def buscar_dados(tabela):
    try:
        res = requests.get(f"{URL_BASE}{tabela}?select=*&order=id.desc", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            # Pilar: Datas em formato correto para o Python
            for col in ['data_inicio', 'data_consulta', 'data_compra']:
                if not df.empty and col in df.columns: df[col] = pd.to_datetime(df[col])
            return df
    except: pass
    return pd.DataFrame()

# --- 2. INTERFACE E ESTILO (Profissional e Limpo) ---
st.set_page_config(page_title="Gestão de Saúde", layout="centered")
st.markdown("""
    <style>
    .card { background: white; border-radius: 10px; padding: 18px; margin-bottom: 12px; border: 1px solid #eee; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); }
    .label { color: #666; font-size: 0.85rem; margin-bottom: 2px; }
    .value { font-size: 1.2rem; font-weight: bold; color: #2c3e50; margin-top: -5px; }
    .status-tag { padding: 3px 8px; border-radius: 5px; font-size: 0.75rem; font-weight: bold; float: right; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIN E NAVEGAÇÃO (Pilar: Acesso Seguro) ---
if "admin" not in st.session_state: st.session_state.admin = False

with st.sidebar:
    st.title("💊 Gestão")
    if not st.session_state.admin:
        pw = st.text_input("Senha ADM", type="password", key="login_pass")
        if st.button("Acessar", use_container_width=True) or (pw == "1234"):
            if pw == "1234":
                st.session_state.admin = True
                st.rerun()
            elif pw != "": st.error("Senha inválida")
    else:
        st.success("Modo ADM Ativo")
        if st.button("Sair", use_container_width=True):
            st.session_state.admin = False
            st.rerun()
    
    # Chave única para o rádio para não quebrar o código
    aba = st.radio("Navegação:", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"], key="main_nav_radio")

# --- 4. TELAS (Funcionalidades Preservadas) ---

if aba == "Estoque":
    st.subheader("📋 Resumo de Medicamentos")
    df = buscar_dados("remedios")
    if not df.empty:
        hoje = datetime.now()
        for _, r in df.iterrows():
            # Pilar: Lógica de Estoque com Suporte a Doses Fracionadas (Ex: 1.5)
            dias_p = (hoje - r['data_inicio']).days
            estoque_at = max(0.0, float(r['qtd_total']) - (dias_p * float(r['dose_diaria'])))
            dias_r = float(estoque_at / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_f = hoje + timedelta(days=dias_r)
            
            cor = "#27ae60" if dias_r > 7 else "#e67e22" if dias_r > 3 else "#e74c3c"
            txt_status = "OK" if dias_r > 7 else "ALERTA"
            
            st.markdown(f"""
            <div class="card">
                <span class="status-tag" style="background: {cor}22; color: {cor};">{txt_status}</span>
                <div style="font-weight:bold; color:#34495e; font-size: 1.1rem;">💊 {r['nome'].upper()}</div>
                <hr style="margin: 12px 0; border:0; border-top:1px solid #f5f5f5;">
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div><p class="label">Qtd</p><p class="value">{estoque_at:g}</p></div>
                    <div><p class="label">Dose/Dia</p><p class="value">{r['dose_diaria']:g}</p></div>
                    <div><p class="label">Restam</p><p class="value">{int(dias_r)}d</p></div>
                    <div><p class="label">Acaba em</p><p class="value">{data_f.strftime('%d/%m/%Y')}</p></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.admin:
                with st.expander(f"Ajustar {r['nome']}"):
                    c1, c2 = st.columns(2)
                    add = c1.number_input("Adicionar Qtd", 0.0, 500.0, 30.0, key=f"add_{r['id']}")
                    prc = c2.number_input("Preço R$", 0.0, 50000.0, float(r['preco']), key=f"prc_{r['id']}")
                    if st.button("Salvar Ajuste", key=f"btn_{r['id']}"):
                        nova_qtd = estoque_at + add
                        requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": nova_qtd, "data_inicio": str(hoje.date()), "preco": prc})
                        requests.post(f"{URL_BASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": prc, "data_compra": str(hoje.date())})
                        enviar_telegram(f"✅ Estoque de {r['nome']} atualizado para {nova_qtd:g} unidades.")
                        st.cache_data.clear(); st.rerun()

elif aba == "Financeiro":
    st.subheader("💰 Controle de Gastos")
    df_r, df_c = buscar_dados("compras"), buscar_dados("consultas")
    
    financeiro = []
    if not df_r.empty:
        r_t = df_r[['data_compra', 'valor']].rename(columns={'data_compra': 'Data'})
        r_t['Tipo'] = 'Remédios'
        financeiro.append(r_t)
    if not df_c.empty:
        c_t = df_c[['data_consulta', 'valor']].rename(columns={'data_consulta': 'Data'})
        c_t['Tipo'] = 'Consultas'
        financeiro.append(c_t)
    
    if financeiro:
        df_fin = pd.concat(financeiro)
        df_fin['Mês'] = df_fin['Data'].dt.strftime('%m/%Y')
        # Gráfico por ano/mês e categoria (Remédios vs Consultas)
        st.bar_chart(df_fin.groupby(['Mês', 'Tipo'])['valor'].sum().reset_index(), x="Mês", y="valor", color="Tipo")
        st.metric("Total Investido", f"R$ {df_fin['valor'].sum():,.2f}")
    else: st.info("Sem dados financeiros registrados.")

elif aba == "Consultas":
    st.subheader("🩺 Histórico de Consultas")
    df = buscar_dados("consultas")
    if not df.empty:
        for _, c in df.iterrows():
            st.info(f"📅 **{c['data_consulta'].strftime('%d/%m/%Y')}** | {c['medico']} | R$ {c['valor']:.2f}")

elif aba == "Cadastrar":
    if st.session_state.admin:
        sel = st.radio("Tipo de Cadastro:", ["Medicamento", "Consulta"], horizontal=True, key="cad_tipo")
        with st.form("form_novo", clear_on_submit=True):
            if sel == "Medicamento":
                n = st.text_input("Nome")
                q = st.number_input("Qtd Inicial", 0.0, step=0.5)
                d = st.number_input("Dose Diária (Ex: 1.5)", 0.0, step=0.5)
                p = st.number_input("Preço R$", 0.0)
                if st.form_submit_button("Salvar Medicamento"):
                    if n and q > 0:
                        requests.post(f"{URL_BASE}remedios", headers=HEADERS, json={"nome":n, "qtd_total":float(q), "dose_diaria":float(d), "preco":float(p), "data_inicio":str(datetime.now().date())})
                        enviar_telegram(f"🆕 Novo remédio cadastrado: {n}")
                        st.cache_data.clear(); st.rerun()
            else:
                m = st.text_input("Médico / Clínica")
                v = st.number_input("Valor R$", 0.0)
                dt = st.date_input("Data da Consulta")
                if st.form_submit_button("Salvar Consulta"):
                    if m:
                        requests.post(f"{URL_BASE}consultas", headers=HEADERS, json={"medico":m, "valor":float(v), "data_consulta":str(dt)})
                        st.cache_data.clear(); st.rerun()
    else: st.warning("Área restrita ao administrador.")

elif aba == "Remover":
    if st.session_state.admin:
        tab = st.selectbox("Remover de:", ["remedios", "consultas"], key="del_tab")
        df_del = buscar_dados(tab)
        if not df_del.empty:
            col = 'nome' if tab == 'remedios' else 'medico'
            item = st.selectbox("Selecione o registro:", df_del[col].tolist(), key="del_item")
            if st.button("🗑️ Excluir Registro", type="primary", use_container_width=True):
                id_id = df_del[df_del[col] == item]['id'].values[0]
                requests.delete(f"{URL_BASE}{tab}?id=eq.{id_id}", headers=HEADERS)
                st.cache_data.clear(); st.rerun()
