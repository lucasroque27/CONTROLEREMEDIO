import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

# --- 1. CONFIGURAÇÕES E PILARES ---
URL_BASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
HEADERS = {"apikey": API_KEY, "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}

def enviar_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM/sendMessage", 
                      json={"chat_id": "5256921022", "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

@st.cache_data(ttl=60)
def buscar_dados(tabela):
    try:
        res = requests.get(f"{URL_BASE}{tabela}?select=*&order=id.desc", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            for col in ['data_inicio', 'data_consulta', 'data_compra']:
                if not df.empty and col in df.columns: df[col] = pd.to_datetime(df[col])
            return df
    except: pass
    return pd.DataFrame()

# --- 2. INTERFACE E ESTILO ---
st.set_page_config(page_title="Gestão de Saúde", layout="centered")
st.markdown("""
    <style>
    .card { background: white; border-radius: 10px; padding: 15px; margin-bottom: 10px; border: 1px solid #eee; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .label { color: #666; font-size: 0.8rem; margin-bottom: 0px; }
    .value { font-size: 1.3rem; font-weight: bold; color: #333; margin-top: -5px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIN E NAVEGAÇÃO ---
if "admin" not in st.session_state: st.session_state.admin = False

with st.sidebar:
    st.title("💊 Gestão")
    if not st.session_state.admin:
        pw = st.text_input("Senha", type="password")
        if st.button("Acessar", use_container_width=True) or pw == "1234":
            if pw == "1234":
                st.session_state.admin = True
                st.rerun()
    else:
        if st.button("Sair"): st.session_state.admin = False; st.rerun()
    
    aba = st.radio("Ir para:", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"], key="nav_main")

# --- 4. TELAS ---

if aba == "Estoque":
    st.subheader("📋 Resumo de Medicamentos")
    df = buscar_dados("remedios")
    if not df.empty:
        hoje = datetime.now()
        for _, r in df.iterrows():
            # Cálculo de Estoque
            dias_passados = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_passados * r['dose_diaria'])))
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)
            
            # HTML Limpo (Sem vazamentos)
            status_color = "#27ae60" if dias_restantes > 7 else "#e74c3c"
            st.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content: space-between;">
                    <span style="font-weight:bold; color:{status_color}">● {r['nome']}</span>
                    <span style="font-size:0.8rem; color:#999">{dias_restantes} dias restantes</span>
                </div>
                <hr style="margin: 10px 0; border:0; border-top:1px solid #eee;">
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div><p class="label">Qtd</p><p class="value">{estoque_atual}</p></div>
                    <div><p class="label">Dose/Dia</p><p class="value">{r['dose_diaria']}</p></div>
                    <div><p class="label">Fim em</p><p class="value">{data_fim.strftime('%d/%m/%Y')}</p></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.admin:
                with st.expander(f"Ajustar estoque de {r['nome']}"):
                    c1, c2 = st.columns(2)
                    add_qtd = c1.number_input("Adicionar Qtd", 0, 1000, 30, key=f"add_{r['id']}")
                    novo_preco = c2.number_input("Preço R$", 0.0, 100000.0, float(r['preco']), key=f"prc_{r['id']}")
                    if st.button("Atualizar", key=f"btn_{r['id']}"):
                        nova_qtd = estoque_atual + add_qtd
                        requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={"qtd_total": nova_qtd, "data_inicio": str(hoje.date()), "preco": novo_preco})
                        requests.post(f"{URL_BASE}compras", headers=HEADERS, json={"nome_remedio": r['nome'], "valor": novo_preco, "data_compra": str(hoje.date())})
                        enviar_telegram(f"✅ Estoque de {r['nome']} atualizado para {nova_qtd} unidades.")
                        st.cache_data.clear(); st.rerun()

elif aba == "Financeiro":
    st.subheader("💰 Controle de Gastos")
    df_r, df_c = buscar_dados("compras"), buscar_dados("consultas")
    
    gastos = []
    if not df_r.empty:
        temp_r = df_r[['data_compra', 'valor']].rename(columns={'data_compra': 'Data'})
        temp_r['Categoria'] = 'Remédio'
        gastos.append(temp_r)
    if not df_c.empty:
        temp_c = df_c[['data_consulta', 'valor']].rename(columns={'data_consulta': 'Data'})
        temp_c['Categoria'] = 'Consulta'
        gastos.append(temp_c)
    
    if gastos:
        df_g = pd.concat(gastos)
        df_g['Mês'] = df_g['Data'].dt.strftime('%m/%Y')
        st.bar_chart(df_g.groupby(['Mês', 'Categoria'])['valor'].sum().reset_index(), x="Mês", y="valor", color="Categoria")
        st.metric("Total Acumulado", f"R$ {df_g['valor'].sum():,.2f}")
    else: st.info("Sem registros.")

elif aba == "Consultas":
    st.subheader("🩺 Histórico de Consultas")
    df = buscar_dados("consultas")
    if not df.empty:
        for _, c in df.iterrows():
            st.success(f"**{c['medico']}** | 📅 {c['data_consulta'].strftime('%d/%m/%Y')} | R$ {c['valor']:.2f}")

elif aba == "Cadastrar":
    if st.session_state.admin:
        tipo = st.radio("O que deseja cadastrar?", ["Novo Remédio", "Nova Consulta"], horizontal=True)
        with st.form("form_cadastro", clear_on_submit=True):
            if tipo == "Novo Remédio":
                nome = st.text_input("Nome do Medicamento")
                qtd = st.number_input("Qtd Inicial", 1)
                dose = st.number_input("Dose Diária", 0.5)
                preco = st.number_input("Preço R$", 0.0, 100000.0)
                if st.form_submit_button("Salvar Medicamento"):
                    if nome:
                        res = requests.post(f"{URL_BASE}remedios", headers=HEADERS, json={"nome": nome, "qtd_total": qtd, "dose_diaria": dose, "preco": preco, "data_inicio": str(datetime.now().date())})
                        if res.status_code in [200, 201]:
                            enviar_telegram(f"🆕 Cadastrado: {nome}"); st.cache_data.clear(); st.success("Salvo!"); st.rerun()
            else:
                med = st.text_input("Médico / Especialidade")
                vlr = st.number_input("Valor da Consulta", 0.0, 100000.0)
                dt_c = st.date_input("Data da Consulta", format="DD/MM/YYYY")
                if st.form_submit_button("Salvar Consulta"):
                    if med:
                        res = requests.post(f"{URL_BASE}consultas", headers=HEADERS, json={"medico": med, "valor": vlr, "data_consulta": str(dt_c)})
                        if res.status_code in [200, 201]:
                            st.cache_data.clear(); st.success("Consulta Salva!"); st.rerun()
    else: st.warning("Acesse com a senha para cadastrar.")

elif aba == "Remover":
    if st.session_state.admin:
        op = st.selectbox("Apagar de:", ["remedios", "consultas"])
        df_del = buscar_dados(op)
        if not df_del.empty:
            label_col = 'nome' if op == 'remedios' else 'medico'
            item = st.selectbox("Escolha o registro:", df_del[label_col].tolist())
            if st.button("🗑️ Confirmar Exclusão", type="primary"):
                id_item = df_del[df_del[label_col] == item]['id'].values[0]
                requests.delete(f"{URL_BASE}{op}?id=eq.{id_item}", headers=HEADERS)
                st.cache_data.clear(); st.rerun()
