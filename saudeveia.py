import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import io

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

# --- 2. INTERFACE ---
st.set_page_config(page_title="Saúde Rock - Pro", layout="centered")
if "autenticado" not in st.session_state: st.session_state.autenticado = False

with st.sidebar:
    st.title("🛡️ Controle")
    if not st.session_state.autenticado:
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar") or senha == "1234":
            if senha == "1234": st.session_state.autenticado = True; st.rerun()
    else:
        if st.button("Sair"): st.session_state.autenticado = False; st.rerun()
    
    st.divider()
    aba = st.radio("Menu", ["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"])

# --- 3. FUNCIONALIDADES ---

if aba == "Estoque":
    st.subheader("📋 Status do Estoque")
    df = buscar_dados("remedios")
    if not df.empty:
        hoje = datetime.now()
        for _, r in df.iterrows():
            ini = pd.to_datetime(r['data_inicio'])
            passados = (hoje - ini).days
            dose = float(r['dose_diaria'])
            # Pilar: Dose 1.5 e cálculo preciso
            atual = max(0.0, float(r['qtd_total']) - (passados * dose))
            resta = float(atual / dose) if dose > 0 else 0
            
            with st.container(border=True):
                st.markdown(f"### 💊 {r['nome'].upper()}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Em mãos", f"{atual:g}")
                c2.metric("Dose/Dia", f"{dose:g}")
                c3.metric("Dias Resta", int(resta))
                
                if st.session_state.autenticado:
                    with st.expander("Ajustar / Comprar"):
                        v_add = st.number_input("Qtd Adquirida", 0.0, key=f"add_{r['id']}")
                        v_pago = st.number_input("Preço da Compra R$", 0.0, key=f"v_{r['id']}")
                        if st.button("Salvar Ajuste", key=f"btn_{r['id']}", use_container_width=True):
                            requests.patch(f"{URL_BASE}remedios?id=eq.{r['id']}", headers=HEADERS, 
                                           json={"qtd_total": float(atual + v_add), "data_inicio": hoje.strftime('%Y-%m-%d')})
                            requests.post(f"{URL_BASE}compras", headers=HEADERS, 
                                           json={"nome_remedio": r['nome'], "valor": float(v_pago), "data_compra": hoje.strftime('%Y-%m-%d')})
                            enviar_telegram(f"✅ Compra: {r['nome']} (+{v_add} un) | R$ {v_pago:.2f}")
                            st.success("Estoque e Financeiro atualizados!"); st.cache_data.clear(); time.sleep(1.5); st.rerun()

elif aba == "Financeiro":
    st.subheader("💰 Controle de Gastos Mensal/Anual")
    df_com = buscar_dados("compras")
    df_con = buscar_dados("consultas")
    
    if not df_com.empty or not df_con.empty:
        # Preparar datas para filtro
        if not df_com.empty: df_com['data'] = pd.to_datetime(df_com['data_compra'])
        if not df_con.empty: df_con['data'] = pd.to_datetime(df_con['data_consulta'])
        
        # Filtros de interface
        c1, c2 = st.columns(2)
        ano_sel = c1.selectbox("Ano", [2024, 2025, 2026], index=2)
        mes_sel = c2.selectbox("Mês", list(range(1, 13)), index=datetime.now().month - 1)
        
        # Lógica de Filtro
        f_com = df_com[(df_com['data'].dt.year == ano_sel) & (df_com['data'].dt.month == mes_sel)] if not df_com.empty else pd.DataFrame()
        f_con = df_con[(df_con['data'].dt.year == ano_sel) & (df_con['data'].dt.month == mes_sel)] if not df_con.empty else pd.DataFrame()
        
        tot_r = f_com['valor'].sum() if not f_com.empty else 0
        tot_c = f_con['valor'].sum() if not f_con.empty else 0
        
        st.divider()
        st.markdown(f"#### Gastos em {mes_sel}/{ano_sel}:")
        col1, col2 = st.columns(2)
        col1.metric("Medicamentos", f"R$ {tot_r:,.2f}")
        col2.metric("Consultas", f"R$ {tot_c:,.2f}")
        st.metric("TOTAL NO MÊS", f"R$ {tot_r + tot_c:,.2f}")
        
        st.divider()
        # BOTÃO DE EXPORTAR (Pilar: Controle de dados)
        if st.button("📥 Exportar Relatório Completo (CSV)"):
            # Une tudo para exportar
            relatorio = pd.concat([df_com, df_con], sort=False)
            csv = relatorio.to_csv(index=False).encode('utf-8')
            st.download_button(label="Clique para baixar planilha", data=csv, file_name=f"saude_rock_{ano_sel}_{mes_sel}.csv", mime="text/csv")

elif aba == "Consultas":
    st.subheader("🩺 Histórico de Consultas")
    df = buscar_dados("consultas")
    if not df.empty:
        st.dataframe(df[['data_consulta', 'medico', 'valor']], hide_index=True, use_container_width=True)

elif aba == "Cadastrar":
    if st.session_state.autenticado:
        opcao = st.selectbox("Tipo:", ["Remédio", "Consulta"])
        with st.form("f_cad"):
            if opcao == "Remédio":
                n, q, d, p = st.text_input("Nome"), st.number_input("Quantidade"), st.number_input("Dose Diária"), st.number_input("Preço")
                if st.form_submit_button("SALVAR"):
                    requests.post(f"{URL_BASE}remedios", headers=HEADERS, json={"nome": n, "qtd_total": float(q), "dose_diaria": float(d), "data_inicio": datetime.now().strftime('%Y-%m-%d')})
                    requests.post(f"{URL_BASE}compras", headers=HEADERS, json={"nome_remedio": n, "valor": float(p), "data_compra": datetime.now().strftime('%Y-%m-%d')})
                    enviar_telegram(f"🆕 Novo Cadastro: {n}")
                    st.success("Salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()
            else:
                m, v = st.text_input("Médico"), st.number_input("Valor")
                if st.form_submit_button("SALVAR"):
                    requests.post(f"{URL_BASE}consultas", headers=HEADERS, json={"medico": m, "valor": float(v), "data_consulta": datetime.now().strftime('%Y-%m-%d')})
                    st.success("Salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()

elif aba == "Remover":
    if st.session_state.autenticado:
        tab = st.selectbox("Onde remover?", ["remedios", "consultas", "compras"])
        df_del = buscar_dados(tab)
        if not df_del.empty:
            c = 'nome' if tab == 'remedios' else ('nome_remedio' if tab == 'compras' else 'medico')
            it = st.selectbox("Selecione:", df_del[c].tolist())
            if st.button("🗑️ EXCLUIR"):
                id_i = df_del[df_del[c] == it]['id'].values[0]
                requests.delete(f"{URL_BASE}{tab}?id=eq.{id_i}", headers=HEADERS)
                st.cache_data.clear(); time.sleep(1); st.rerun()
