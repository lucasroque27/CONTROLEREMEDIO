import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import time

# --- 1. CONFIGURAÇÕES TÉCNICAS ---
URL_SUPABASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
HEADERS = {
    "apikey": API_KEY, 
    "Authorization": f"Bearer {API_KEY}", 
    "Content-Type": "application/json", 
    "Prefer": "return=representation"
}

# --- 2. FUNÇÕES DE DADOS ---
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

# --- 3. INTERFACE E MENU ---
st.set_page_config(page_title="Saúde Rock", page_icon="💊", layout="wide")

with st.sidebar:
    st.title("🛡️ Gestão de Saúde")
    if "admin" not in st.session_state: st.session_state.admin = False
    
    # Sistema de Login para proteção de dados
    if not st.session_state.admin:
        senha = st.text_input("Senha Administrativa", type="password")
        if st.button("Acessar Painel"):
            if senha == "1234":
                st.session_state.admin = True
                st.rerun()
            else: st.error("Senha incorreta")
    else:
        st.success("Modo Editor Ativo")
        if st.button("Sair"):
            st.session_state.admin = False
            st.rerun()

    menu = st.radio("Navegação:", ["📦 Estoque", "🩺 Consultas", "💰 Financeiro", "➕ Cadastro", "🗑️ Remover"])

# Tradução para meses em PT-BR
meses_pt = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}

# --- 4. TELAS DO SISTEMA ---

# TELA 1: ESTOQUE (A que você mais usa)
if menu == "📦 Estoque":
    st.header("📋 Resumo de Medicamentos")
    df = api_get("remedios")
    
    if df.empty:
        st.info("Nenhum medicamento cadastrado ainda.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            # Cálculos automáticos de estoque e datas
            dias_p = (hoje - r['data_inicio']).days
            estoque_atual = max(0, int(r['qtd_total'] - (dias_p * r['dose_diaria'])))
            dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_termino = hoje + timedelta(days=dias_restantes)
            
            with st.container(border=True):
                # Cabeçalho do Card
                c_tit, c_status = st.columns([3, 1])
                c_tit.subheader(f"💊 {r['nome'].upper()}")
                
                if dias_restantes < 7: c_status.error("🆘 REPOR AGORA")
                elif dias_restantes < 15: c_status.warning("⚠️ ATENÇÃO")
                else: c_status.success("✅ ESTOQUE BOM")

                # Grid de Resumo (O que você pediu: Qtd, Dose, Dias, Data)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Quantidade", f"{estoque_atual} un.")
                m2.metric("Dose Diária", f"{r['dose_diaria']}")
                m3.metric("Dias de Dose", f"{dias_restantes}")
                m4.metric("Acaba em", f"{data_termino.day}/{meses_pt[data_termino.month]}")
                
                st.write(f"💰 **Preço da última compra:** R$ {r['preco']:.2f}")

                # FUNCIONALIDADE: Ajuste de Medicamento (Preço + Qtd)
                if st.session_state.admin:
                    with st.expander(f"⚙️ Atualizar {r['nome']}"):
                        col_q, col_p = st.columns(2)
                        add_q = col_q.number_input("Qtd comprada", 1, 500, 30, key=f"q_{r['id']}")
                        add_p = col_p.number_input("Novo Preço R$", 0.0, 5000.0, float(r['preco']), key=f"p_{r['id']}")
                        
                        if st.button("Salvar Reposição", key=f"b_{r['id']}"):
                            nova_qtd_total = estoque_atual + add_q
                            # Atualiza o remédio
                            requests.patch(f"{URL_SUPABASE}remedios?id=eq.{r['id']}", headers=HEADERS, json={
                                "qtd_total": int(nova_qtd_total), 
                                "data_inicio": str(hoje.date()),
                                "preco": float(add_p)
                            })
                            # Registra no financeiro automaticamente
                            requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={
                                "nome_remedio": r['nome'], "valor": float(add_p), "data_compra": str(hoje.date())
                            })
                            st.success("Estoque e Financeiro atualizados!"); time.sleep(1); st.rerun()

# TELA 2: CONSULTAS
elif menu == "🩺 Consultas":
    st.header("🩺 Histórico de Consultas")
    df_c = api_get("consultas")
    if df_c.empty:
        st.info("Nenhuma consulta registrada.")
    else:
        for _, c in df_c.iterrows():
            with st.container(border=True):
                st.write(f"**Médico/Especialidade:** {c['medico']}")
                st.write(f"📅 **Data:** {c['data_consulta'].strftime('%d/%m/%Y')} | 💸 **Valor:** R$ {c['valor']:.2f}")

# TELA 3: FINANCEIRO
elif menu == "💰 Financeiro":
    st.header("💰 Controle de Gastos")
    df_compras = api_get("compras")
    df_consultas = api_get("consultas")
    
    t_meds = df_compras['valor'].sum() if not df_compras.empty else 0
    t_cons = df_consultas['valor'].sum() if not df_consultas.empty else 0
    
    c1, c2 = st.columns(2)
    c1.metric("Total em Remédios", f"R$ {t_meds:.2f}")
    c2.metric("Total em Consultas", f"R$ {t_cons:.2f}")
    st.subheader(f"Gasto Total Acumulado: R$ {t_meds + t_cons:.2f}")
    
    if not df_compras.empty:
        with st.expander("Ver detalhamento de compras"):
            st.dataframe(df_compras[['data_compra', 'nome_remedio', 'valor']], use_container_width=True)

# TELA 4: CADASTRO
elif menu == "➕ Cadastro":
    st.header("➕ Cadastrar Novo")
    if not st.session_state.admin:
        st.warning("Acesse com a senha na lateral para cadastrar.")
    else:
        tipo = st.selectbox("O que deseja cadastrar?", ["Remédio", "Consulta"])
        with st.form("form_cad"):
            if tipo == "Remédio":
                n = st.text_input("Nome do Medicamento")
                col1, col2, col3 = st.columns(3)
                q = col1.number_input("Qtd na Caixa", 1)
                d = col2.number_input("Dose Diária", 0.1, 10.0, 1.0)
                p = col3.number_input("Preço Pago R$", 0.0)
                if st.form_submit_button("Salvar Remédio"):
                    requests.post(f"{URL_SUPABASE}remedios", headers=HEADERS, json={"nome":n,"qtd_total":int(q),"dose_diaria":float(d),"preco":float(p),"data_inicio":str(datetime.now().date())})
                    requests.post(f"{URL_SUPABASE}compras", headers=HEADERS, json={"nome_remedio":n,"valor":float(p),"data_compra":str(datetime.now().date())})
                    st.success("Cadastrado!"); time.sleep(1); st.rerun()
            else:
                m = st.text_input("Médico / Clínica")
                v = st.number_input("Valor da Consulta R$", 0.0)
                if st.form_submit_button("Salvar Consulta"):
                    requests.post(f"{URL_SUPABASE}consultas", headers=HEADERS, json={"medico":m, "valor":float(v), "data_consulta":str(datetime.now().date())})
                    st.success("Registrado!"); time.sleep(1); st.rerun()

# TELA 5: REMOVER
elif menu == "🗑️ Remover":
    st.header("🗑️ Excluir Registros")
    if not st.session_state.admin:
        st.error("Área restrita.")
    else:
        tabela_del = st.selectbox("Categoria", ["remedios", "consultas", "compras"])
        df_del = api_get(tabela_del)
        if not df_del.empty:
            # Identifica a coluna de nome correta para o selectbox
            col_nome = 'nome' if tabela_del == 'remedios' else 'medico' if tabela_del == 'consultas' else 'nome_remedio'
            item_del = st.selectbox("Selecione o item para apagar", df_del[col_nome].tolist())
            if st.button("EXCLUIR PERMANENTEMENTE"):
                id_alvo = df_del[df_del[col_nome] == item_del]['id'].values[0]
                requests.delete(f"{URL_SUPABASE}{tabela_del}?id=eq.{id_alvo}", headers=HEADERS)
                st.success("Apagado com sucesso!"); time.sleep(1); st.rerun()
