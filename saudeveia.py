import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURAÇÃO DE CONEXÃO ---
# Mantive suas chaves originais que estavam funcionando
URL_BASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
HEADERS = {
    "apikey": API_KEY, 
    "Authorization": f"Bearer {API_KEY}", 
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# --- 2. FUNÇÕES DE DADOS (COM TRATAMENTO DE ERRO) ---
@st.cache_data(ttl=1)
def buscar_dados(tabela):
    try:
        response = requests.get(f"{URL_BASE}{tabela}?select=*", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            st.error(f"Erro ao acessar {tabela}: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Falha de conexão: {e}")
        return pd.DataFrame()

# --- 3. INTERFACE PRINCIPAL ---
st.set_page_config(page_title="Gestão Saúde", layout="centered")

# Garantir que o estado do login exista
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# Barra Lateral
with st.sidebar:
    st.header("🔑 Acesso")
    if not st.session_state.autenticado:
        senha = st.text_input("Digite a senha", type="password")
        if st.button("Entrar") or (senha == "1234"):
            if senha == "1234":
                st.session_state.autenticado = True
                st.rerun()
            elif senha != "":
                st.error("Senha incorreta")
    else:
        st.success("Modo Administrador")
        if st.button("Sair"):
            st.session_state.autenticado = False
            st.rerun()
    
    st.divider()
    aba = st.radio("Navegação", ["Estoque", "Financeiro", "Cadastrar", "Remover"])

# --- 4. TELAS DO SISTEMA ---

if aba == "Estoque":
    st.subheader("📋 Status do Estoque")
    df = buscar_dados("remedios")
    
    if df.empty:
        st.info("Nenhum remédio encontrado ou erro na conexão.")
    else:
        hoje = datetime.now()
        for _, r in df.iterrows():
            # PILARES: Cálculo de dose fracionada (1.5) e data de término
            data_ini = pd.to_datetime(r['data_inicio'])
            dias_corridos = (hoje - data_ini).days
            qtd_atual = max(0.0, float(r['qtd_total']) - (dias_corridos * float(r['dose_diaria'])))
            
            dias_restantes = float(qtd_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
            data_fim = hoje + timedelta(days=dias_restantes)
            
            with st.expander(f"💊 {r['nome'].upper()}", expanded=True):
                c1, c2, c3 = st.columns(3)
                c1.metric("Estoque", f"{qtd_atual:g}")
                c2.metric("Dose/Dia", f"{r['dose_diaria']:g}")
                c3.write(f"Acaba em: \n**{data_fim.strftime('%Y-%m-%d')}**")
                
                if st.session_state.autenticado:
                    v_add = st.number_input("Adicionar Qtd", 0.0, key=f"add_{r['id']}")
                    v_prc = st.number_input("Preço Atual", 0.0, value=float(r['preco']), key=f"prc_{r['id']}")
                    if st.button("Atualizar", key=f"btn_{r['id']}"):
                        payload = {
                            "qtd_total": float(qtd_atual + v_add),
                            "data_inicio": hoje.strftime('%Y-%m-%d'),
                            "preco": float(v_prc)
                        }
                        res = requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, json=payload)
                        if res.status_code in [200, 204]:
                            st.success("Atualizado!")
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()

elif aba == "Financeiro":
    st.subheader("💰 Resumo Financeiro")
    df_r = buscar_dados("remedios")
    df_c = buscar_dados("consultas")
    
    # PILAR: Financeiro Dinâmico
    tot_r = df_r['preco'].sum() if not df_r.empty else 0
    tot_c = df_c['valor'].sum() if not df_c.empty else 0
    
    st.metric("Investimento Total", f"R$ {tot_r + tot_c:,.2f}")
    
    if not df_r.empty:
        st.write("Gastos por Remédio")
        st.bar_chart(df_r, x="nome", y="preco")

elif aba == "Cadastrar":
    if not st.session_state.autenticado:
        st.warning("Acesse com a senha na barra lateral para cadastrar.")
    else:
        tipo = st.radio("O que cadastrar?", ["Remédio", "Consulta"])
        with st.form("form_cadastro"):
            if tipo == "Remédio":
                n = st.text_input("Nome do Remédio")
                q = st.number_input("Quantidade Total", 0.0)
                d = st.number_input("Dose Diária", 0.0)
                p = st.number_input("Preço R$", 0.0)
                if st.form_submit_button("SALVAR"):
                    if n:
                        payload = {
                            "nome": n, "qtd_total": float(q), "dose_diaria": float(d), 
                            "preco": float(p), "data_inicio": datetime.now().strftime('%Y-%m-%d')
                        }
                        res = requests.post(f"{URL_BASE}remedios", headers=HEADERS, json=payload)
                        if res.status_code in [200, 201]:
                            st.success("Salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()
            else:
                m = st.text_input("Médico")
                v = st.number_input("Valor R$", 0.0)
                if st.form_submit_button("SALVAR"):
                    payload = {"medico": m, "valor": float(v), "data_consulta": datetime.now().strftime('%Y-%m-%d')}
                    res = requests.post(f"{URL_BASE}consultas", headers=HEADERS, json=payload)
                    if res.status_code in [200, 201]:
                        st.success("Salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()

elif aba == "Remover":
    if not st.session_state.autenticado:
        st.warning("Acesse com a senha para remover itens.")
    else:
        tabela = st.selectbox("Escolha a categoria", ["remedios", "consultas"])
        df_del = buscar_dados(tabela)
        if not df_del.empty:
            campo = "nome" if tabela == "remedios" else "medico"
            item = st.selectbox("Selecione o item", df_del[campo].tolist())
            if st.button("🗑️ EXCLUIR DEFINITIVAMENTE"):
                id_item = df_del[df_del[campo] == item]['id'].values[0]
                res = requests.delete(f"{URL_BASE}{tabela}?id=eq.{id_item}", headers=HEADERS)
                if res.status_code in [200, 204]:
                    st.success("Removido!"); st.cache_data.clear(); time.sleep(1); st.rerun()
