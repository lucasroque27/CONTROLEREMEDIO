import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURAÇÕES ---
URL_BASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
HEADERS = {
    "apikey": API_KEY, 
    "Authorization": f"Bearer {API_KEY}", import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURAÇÕES ---
URL_BASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
HEADERS = {
    "apikey": API_KEY, 
    "Authorization": f"Bearer {API_KEY}", 
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def enviar_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM/sendMessage", 
                      json={"chat_id": "5256921022", "text": msg}, timeout=5)
    except: pass

@st.cache_data(ttl=1)
def buscar_dados(tabela):
    try:
        res = requests.get(f"{URL_BASE}{tabela}?select=*", headers=HEADERS, timeout=10)
        return pd.DataFrame(res.json()) if res.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

# --- 2. INTERFACE E SETUP PARA MOBILE ---
# O layout 'centered' é o melhor para celular
st.set_page_config(page_title="Saúde Rock - App", layout="centered", initial_sidebar_state="collapsed")

if "autenticado" not in st.session_state: st.session_state.autenticado = False
if "alertas_enviados" not in st.session_state: st.session_state.alertas_enviados = []

# --- BARRA LATERAL (APENAS PARA LOGIN/CONFIG) ---
with st.sidebar:
    st.title("🔒 Área Restrita")
    st.caption("Acesse para Cadastrar, Remover ou Ajustar Estoque.")
    if not st.session_state.autenticado:
        senha = st.text_input("Senha ADM", type="password")
        if st.button("Acessar", use_container_width=True) or senha == "1234":
            if senha == "1234": st.session_state.autenticado = True; st.rerun()
    else:
        st.success("Logado como ADM")
        if st.button("Sair do Modo ADM", use_container_width=True):
            st.session_state.autenticado = False; st.rerun()

# --- CABEÇALHO E MENU SUPERIOR RESPONSIVO ---
st.markdown("<h2 style='text-align: center; padding-bottom: 10px;'>📱 Gestão de Saúde</h2>", unsafe_allow_html=True)

# Este é o segredo para o celular: horizontal=True adapta os botões lado a lado
aba = st.radio(
    "Navegação", 
    ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"], 
    horizontal=True, 
    label_visibility="collapsed" # Esconde a palavra "Navegação" para poupar espaço na tela
)

st.divider()

# --- 3. TELAS (FUNCIONALIDADES INTACTAS) ---

if aba == "Estoque":
    st.subheader("📋 Estoque e Previsões")
    df = buscar_dados("remedios")
    if not df.empty:
        hoje = datetime.now()
        for _, r in df.iterrows():
            ini = pd.to_datetime(r['data_inicio'])
            passados = (hoje - ini).days
            dose = float(r['dose_diaria'])
            atual = max(0.0, float(r['qtd_total']) - (passados * dose))
            resta_dias = float(atual / dose) if dose > 0 else 0
            data_fim = hoje + timedelta(days=resta_dias)
            
            # --- ALERTA TELEGRAM MANTIDO (APENAS 7 DIAS OU ZERO) ---
            if 0 < resta_dias <= 7:
                if r['id'] not in st.session_state.alertas_enviados:
                    enviar_telegram(f"⚠️ ALERTA: O remédio {r['nome'].upper()} acaba em {int(resta_dias)} dias! (Previsão: {data_fim.strftime('%d/%m/%Y')})")
                    st.session_state.alertas_enviados.append(r['id'])
            elif atual <= 0:
                if f"zerado_{r['id']}" not in st.session_state.alertas_enviados:
                    enviar_telegram(f"🚨 ALERTA: O remédio {r['nome'].upper()} ESTÁ ZERADO!")
                    st.session_state.alertas_enviados.append(f"zerado_{r['id']}")
            # --------------------------------------------------------

            with st.container(border=True):
                st.markdown(f"### 💊 {r['nome'].upper()}")
                
                # As colunas empilham naturalmente no celular se não couberem
                c1, c2, c3 = st.columns(3)
                c1.metric("Estoque", f"{atual:g}")
                c2.metric("Dose", f"{dose:g}")
                c3.metric("Resta (Dias)", int(resta_dias))
                
                if atual > 0:
                    st.warning(f"📅 **Término: {data_fim.strftime('%d/%m/%Y')}**")
                else:
                    st.error("🚨 **ESTOQUE ZERADO**")
                
                if st.session_state.autenticado:
                    with st.expander("➕ Ajustar Estoque / Nova Compra"):
                        v_add = st.number_input("Comprado (Qtd)", 0.0, key=f"add_{r['id']}")
                        v_pago = st.number_input("Valor Pago (R$)", 0.0, key=f"v_{r['id']}")
                        if st.button("Confirmar Compra", key=f"btn_{r['id']}", use_container_width=True):
                            requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, 
                                           json={"qtd_total": float(atual + v_add), "data_inicio": hoje.strftime('%Y-%m-%d')})
                            requests.post(f"{URL_BASE}compras", headers=HEADERS, 
                                           json={"nome_remedio": r['nome'], "valor": float(v_pago), "data_compra": hoje.strftime('%Y-%m-%d')})
                            
                            st.success("Atualizado!"); st.cache_data.clear(); time.sleep(1.5); st.rerun()

elif aba == "Financeiro":
    st.subheader("💰 Resumo Financeiro")
    df_com = buscar_dados("compras")
    df_con = buscar_dados("consultas")
    
    if not df_com.empty or not df_con.empty:
        if not df_com.empty: df_com['data'] = pd.to_datetime(df_com['data_compra'])
        if not df_con.empty: df_con['data'] = pd.to_datetime(df_con['data_consulta'])
        
        c1, c2 = st.columns(2)
        ano_sel = c1.selectbox("Ano", [2024, 2025, 2026], index=2)
        mes_sel = c2.selectbox("Mês", list(range(1, 13)), index=datetime.now().month - 1)
        
        f_com = df_com[(df_com['data'].dt.year == ano_sel) & (df_com['data'].dt.month == mes_sel)] if not df_com.empty else pd.DataFrame()
        f_con = df_con[(df_con['data'].dt.year == ano_sel) & (df_con['data'].dt.month == mes_sel)] if not df_con.empty else pd.DataFrame()
        
        tr, tc = f_com['valor'].sum() if not f_com.empty else 0, f_con['valor'].sum() if not f_con.empty else 0
        
        st.divider()
        col1, col2 = st.columns(2)
        col1.metric("Remédios", f"R$ {tr:,.2f}")
        col2.metric("Consultas", f"R$ {tc:,.2f}")
        st.metric("TOTAL NO MÊS", f"R$ {tr + tc:,.2f}")
        
        st.divider()
        if st.button("📥 Baixar Planilha (CSV)", use_container_width=True):
            relatorio = pd.concat([df_com, df_con], sort=False)
            csv = relatorio.to_csv(index=False).encode('utf-8')
            st.download_button(label="Clique aqui para salvar", data=csv, file_name=f"relatorio_{ano_sel}_{mes_sel}.csv", mime="text/csv", use_container_width=True)

elif aba == "Consultas":
    st.subheader("🩺 Consultas")
    df = buscar_dados("consultas")
    if not df.empty:
        st.dataframe(df[['data_consulta', 'medico', 'valor']], hide_index=True, use_container_width=True)

elif aba == "Cadastrar":
    if st.session_state.autenticado:
        st.subheader("📝 Novo Registro")
        t = st.selectbox("Tipo:", ["Remédio", "Consulta"])
        with st.form("cad_form"):
            if t == "Remédio":
                n, q, d, p = st.text_input("Nome"), st.number_input("Qtd Inicial"), st.number_input("Dose Diária"), st.number_input("Valor da Compra (R$)")
                if st.form_submit_button("Salvar Cadastro", use_container_width=True):
                    requests.post(f"{URL_BASE}remedios", headers=HEADERS, json={"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "data_inicio": datetime.now().strftime('%Y-%m-%d')})
                    requests.post(f"{URL_BASE}compras", headers=HEADERS, json={"nome_remedio": n, "valor": float(p), "data_compra": datetime.now().strftime('%Y-%m-%d')})
                    st.success("Salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()
            else:
                m, v = st.text_input("Médico"), st.number_input("Valor (R$)")
                if st.form_submit_button("Salvar Consulta", use_container_width=True):
                    requests.post(f"{URL_BASE}consultas", headers=HEADERS, json={"medico": m, "valor": float(v), "data_consulta": datetime.now().strftime('%Y-%m-%d')})
                    st.success("Salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()
    else:
        st.info("Acesse a Área Restrita no menu esquerdo para cadastrar.")

elif aba == "Remover":
    if st.session_state.autenticado:
        st.subheader("🗑️ Apagar Registros")
        tab = st.selectbox("Tabela:", ["remedios", "consultas", "compras"])
        df_del = buscar_dados(tab)
        if not df_del.empty:
            campo = 'nome' if tab == 'remedios' else ('nome_remedio' if tab == 'compras' else 'medico')
            it_selecionado = st.selectbox("Selecione para apagar:", df_del[campo].tolist())
            
            if st.button("EXCLUIR DEFINITIVAMENTE", type="primary", use_container_width=True):
                id_item = df_del[df_del[campo] == it_selecionado]['id'].values[0]
                
                if tab == "remedios":
                    nome_rem = it_selecionado
                    requests.delete(f"{URL_BASE}remedios?id=eq.{id_item}", headers=HEADERS)
                    requests.delete(f"{URL_BASE}compras?nome_remedio=eq.{nome_rem}", headers=HEADERS)
                    st.warning(f"Remédio '{nome_rem}' e seus gastos foram excluídos.")
                else:
                    requests.delete(f"{URL_BASE}{tab}?id=eq.{id_item}", headers=HEADERS)
                    st.warning("Registro excluído.")
                
                st.cache_data.clear()
                time.sleep(1.5)
                st.rerun()
    else:
        st.info("Acesse a Área Restrita no menu esquerdo para remover.")
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def enviar_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM/sendMessage", 
                      json={"chat_id": "5256921022", "text": msg}, timeout=5)
    except: pass

@st.cache_data(ttl=1)
def buscar_dados(tabela):
    try:
        res = requests.get(f"{URL_BASE}{tabela}?select=*", headers=HEADERS, timeout=10)
        return pd.DataFrame(res.json()) if res.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

# --- 2. INTERFACE E CSS ANTI-CORTE ---
st.set_page_config(page_title="Saúde Rock", layout="centered")

st.markdown("""
    <style>
    /* Ajuste de margem global para evitar cortes no topo */
    .stApp { margin-top: 0px !important; }
    .block-container { 
        padding-top: 3.5rem !important; 
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Botões táteis */
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    
    /* Grid flexível para métricas */
    .flex-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: space-between;
        margin-bottom: 10px;
    }
    .flex-item {
        flex: 1 1 100px;
        min-width: 85px;
        text-align: center;
        background: rgba(128, 128, 128, 0.05);
        padding: 10px;
        border-radius: 8px;
    }
    
    /* Previne que textos longos quebrem o layout */
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; }
    .flex-grid { display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between; margin-bottom: 10px; }
    .flex-item { flex: 1 1 100px; min-width: 85px; text-align: center; background: rgba(128, 128, 128, 0.05); padding: 10px; border-radius: 8px; }
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    
    /* Ajuste específico para o rótulo do Radio Button que estava cortando */
    [data-testid="stWidgetLabel"] p {
        margin-bottom: 8px !important;
        font-size: 1rem !important;
    }
    [data-testid="stWidgetLabel"] p { margin-bottom: 8px !important; font-size: 1rem !important; }
    </style>
""", unsafe_allow_html=True)

if "autenticado" not in st.session_state: 
    st.session_state.autenticado = False

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ RÉMEDIOS DA VEIA")
    st.title("🛡️ Controle")
    if not st.session_state.autenticado:
        senha = st.text_input("Senha ADM", type="password")
        if st.button("Entrar") or (senha == "1234"):
            if senha == "1234":
                st.session_state.autenticado = True
                st.rerun()
    else:
        if st.button("Sair do ADM"):
            st.session_state.autenticado = False
            st.rerun()

    st.divider()
    aba = st.radio("Navegação", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"])

# --- 4. TELAS ---

if aba == "Estoque":
    st.subheader("📋 MEDICAMENTOS CONTROLE")
    st.subheader("📋 Status do Estoque")
    df = buscar_dados("remedios")
    if not df.empty:
        hoje = datetime.now()
        for _, r in df.iterrows():
            ini = pd.to_datetime(r['data_inicio'])
            passados = (hoje - ini).days
            dose = float(r['dose_diaria'])
            atual = max(0.0, float(r['qtd_total']) - (passados * dose))
            resta_dias = float(atual / dose) if dose > 0 else 0
            data_fim = hoje + timedelta(days=resta_dias)

            # Alerta automático Telegram para estoque baixo
            if resta_dias <= 5 and f"alerta_{r['id']}" not in st.session_state:
                enviar_telegram(f"⚠️ ESTOQUE BAIXO: {r['nome'].upper()} acaba em {int(resta_dias)} dias!")
                st.session_state[f"alerta_{r['id']}"] = True

            with st.container(border=True):
                st.markdown(f"**💊 {r['nome'].upper()}**")
                st.markdown(f"""
                <div class="flex-grid">
                    <div class="flex-item">
                        <div style="font-size:0.7rem; opacity:0.7;">Estoque</div>
                        <div style="font-size:1.1rem; font-weight:bold;">{atual:g}</div>
                    </div>
                    <div class="flex-item">
                        <div style="font-size:0.7rem; opacity:0.7;">Dose/Dia</div>
                        <div style="font-size:1.1rem; font-weight:bold;">{dose:g}</div>
                    </div>
                    <div class="flex-item">
                        <div style="font-size:0.7rem; opacity:0.7;">Dias Rest.</div>
                        <div style="font-size:1.1rem; font-weight:bold;">{int(resta_dias)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if resta_dias > 0:
                    st.caption(f"📅 Fim previsto: {data_fim.strftime('%d/%m/%Y')}")
                else:
                    st.error("🚨 ESTOQUE ZERADO")

                if st.session_state.autenticado:
                    with st.expander("Ajustar / Comprar"):
                        v_add = st.number_input("Qtd Adquirida", 0.0, key=f"add_{r['id']}")
                        v_pago = st.number_input("Valor Pago R$", 0.0, key=f"v_{r['id']}")
                        if st.button("Salvar Ajuste", key=f"btn_{r['id']}"):
                            novo_total = atual + v_add
                            requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, 
                                           json={"qtd_total": float(novo_total), "data_inicio": hoje.strftime('%Y-%m-%d')})
                            if v_pago > 0:
                                requests.post(f"{URL_BASE}compras", headers=HEADERS, 
                                               json={"nome_remedio": r['nome'], "valor": float(v_pago), "data_compra": hoje.strftime('%Y-%m-%d')})
                            if f"alerta_{r['id']}" in st.session_state: del st.session_state[f"alerta_{r['id']}"]
                            enviar_telegram(f"✅ Atualizado: {r['nome']} | Total: {novo_total}")
                            st.success("Atualizado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

elif aba == "Financeiro":
    st.subheader("💰 Gastos Mensais")
    df_com = buscar_dados("compras")
    df_con = buscar_dados("consultas")

    col_sel1, col_sel2 = st.columns(2)
    ano_sel = col_sel1.selectbox("Ano", [2025, 2026], index=1)
    mes_sel = col_sel2.selectbox("Mês", list(range(1, 13)), index=datetime.now().month - 1)

    tr, tc = 0.0, 0.0
    if not df_com.empty:
        df_com['data'] = pd.to_datetime(df_com['data_compra'])
        tr = df_com[(df_com['data'].dt.year == ano_sel) & (df_com['data'].dt.month == mes_sel)]['valor'].sum()
    if not df_con.empty:
        df_con['data'] = pd.to_datetime(df_con['data_consulta'])
        tc = df_con[(df_con['data'].dt.year == ano_sel) & (df_con['data'].dt.month == mes_sel)]['valor'].sum()

    with st.container(border=True):
        st.markdown(f"""
        <div class="flex-grid">
            <div class="flex-item">
                <div style="font-size:0.8rem; opacity:0.7;">💊 Remédios</div>
                <div style="font-size:1.2rem; font-weight:bold;">R$ {tr:,.2f}</div>
            </div>
            <div class="flex-item">
                <div style="font-size:0.8rem; opacity:0.7;">🩺 Consultas</div>
                <div style="font-size:1.2rem; font-weight:bold;">R$ {tc:,.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        st.write("**TOTAL INVESTIDO**")
        st.title(f"R$ {tr + tc:,.2f}")

    if st.button("📥 Gerar Planilha CSV"):
    if st.button("📥 Baixar Relatório CSV"):
        rel = pd.concat([df_com, df_con], sort=False)
        st.download_button("Baixar Agora", rel.to_csv(index=False).encode('utf-8'), "financeiro.csv", "text/csv")
        st.download_button("Clique aqui para baixar", rel.to_csv(index=False).encode('utf-8'), "financeiro.csv", "text/csv")

elif aba == "Consultas":
    st.subheader("🩺 Histórico")
    df = buscar_dados("consultas")
    if not df.empty:
        st.dataframe(df.sort_values('data_consulta', ascending=False), hide_index=True, use_container_width=True)

elif aba == "Cadastrar":
    if st.session_state.autenticado:
        st.subheader("📝 Novo Cadastro")
        # Adicionado espaço extra antes do rádio para evitar corte do rótulo
        st.write("") 
        modo = st.radio("Selecione o tipo:", ["Remédio", "Consulta"])

        with st.form("cad_form"):
            if modo == "Remédio":
                n = st.text_input("Nome do Remédio")
                q = st.number_input("Quantidade em Estoque", 0.0)
                d = st.number_input("Dose Diária", 0.0)
                p = st.number_input("Preço da Compra (R$)", 0.0)
                if st.form_submit_button("Salvar Cadastro"):
                    requests.post(f"{URL_BASE}remedios", headers=HEADERS, json={"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "data_inicio": datetime.now().strftime('%Y-%m-%d')})
                    st.success("Remédio Cadastrado!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                    hoje_str = datetime.now().strftime('%Y-%m-%d')
                    requests.post(f"{URL_BASE}remedios", headers=HEADERS, json={"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "data_inicio": hoje_str})
                    if p > 0:
                        requests.post(f"{URL_BASE}compras", headers=HEADERS, json={"nome_remedio": n, "valor": float(p), "data_compra": hoje_str})
                    st.success("Remédio e Gasto Registrados!"); st.cache_data.clear(); time.sleep(1); st.rerun()
            else:
                md = st.text_input("Nome do Médico / Especialidade")
                md = st.text_input("Médico / Especialidade")
                vl = st.number_input("Valor da Consulta", 0.0)
                if st.form_submit_button("Salvar Cadastro"):
                    requests.post(f"{URL_BASE}consultas", headers=HEADERS, json={"medico": md, "valor": float(vl), "data_consulta": datetime.now().strftime('%Y-%m-%d')})
                    st.success("Consulta Registrada!"); st.cache_data.clear(); time.sleep(1); st.rerun()
    else:
        st.warning("⚠️ Acesse o modo ADM no menu lateral para cadastrar dados.")

elif aba == "Remover":
    if st.session_state.autenticado:
        t = st.selectbox("Tabela para remoção", ["remedios", "consultas", "compras"])
        df_del = buscar_dados(t)
        if not df_del.empty:
            c = 'nome' if t == 'remedios' else ('nome_remedio' if t == 'compras' else 'medico')
            it = st.selectbox("Item para excluir:", df_del[c].tolist())
            if st.button("🗑️ APAGAR PERMANENTEMENTE", type="primary"):
            it = st.selectbox("Item para excluir permanentemente:", df_del[c].tolist())
            if st.button("🗑️ APAGAR AGORA", type="primary"):
                id_it = df_del[df_del[c] == it]['id'].values[0]
                requests.delete(f"{URL_BASE}{t}?id=eq.{id_it}", headers=HEADERS)
                st.success("Excluído com sucesso!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                st.success("Removido com sucesso!"); st.cache_data.clear(); time.sleep(1); st.rerun()
