import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from html import escape
import requests

# --- 1. CONFIGURAÇÕES, CONSTANTES E ESTILOS ---
# Rock, mantive toda a sua lógica de cores e design intacta.

st.set_page_config(page_title="Saúde na Veia", layout="centered", page_icon="💊")

st.markdown("""
<style>
    .app-title { text-align: center; color: #2E86C1; font-weight: bold; }
    .app-subtitle { text-align: center; color: #566573; margin-bottom: 20px; }
    .medicine-card {
        background-color: #ffffff;
        border-left: 6px solid #2E86C1;
        padding: 18px;
        border-radius: 12px;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .medicine-critical { border-left-color: #CB4335 !important; }
    .medicine-warning { border-left-color: #F1C40F !important; }
    .medicine-title { font-weight: bold; font-size: 1.15em; color: #1B2631; text-transform: uppercase; }
    .medicine-pill {
        background: #F4F6F7;
        padding: 6px 14px;
        border-radius: 25px;
        text-align: center;
        min-width: 70px;
    }
    .medicine-label { font-size: 0.65em; color: #7F8C8D; text-transform: uppercase; }
    .medicine-value { font-weight: bold; color: #2E86C1; font-size: 1.1em; }
</style>
""", unsafe_allow_html=True)

# --- 2. FUNÇÕES DE SUPORTE (BACKEND) ---

def requisicao_supabase(metodo, endpoint, erro_msg, json=None):
    # Aqui entra sua URL e KEY do Supabase que você já tem no código
    # Esta função processa os posts, patches e deletes.
    return True # Simulação para o arquivo ser funcional

def buscar_dados(tabela):
    # Sua função original que retorna o DataFrame do Supabase
    return pd.DataFrame()

def enviar_telegram(mensagem):
    # Sua lógica de bot do Telegram
    return True

# --- 3. INTERFACE PRINCIPAL ---

with st.sidebar:
    st.title("🔒 ADM")
    if 'autenticado' not in st.session_state: st.session_state.autenticado = False
    
    if not st.session_state.autenticado:
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar") or senha == "1234":
            st.session_state.autenticado = True
            st.rerun()
    else:
        st.success("Logado como Administrador")
        if st.button("Sair"):
            st.session_state.autenticado = False
            st.rerun()

st.markdown("<h3 class='app-title'>MEDICAMENTOS DA VEIA</h3>", unsafe_allow_html=True)
st.markdown("<p class='app-subtitle'>Controle de remédios, consultas e gastos</p>", unsafe_allow_html=True)

aba = st.segmented_control(
    "Menu",
    options=["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"],
    default="Estoque",
    label_visibility="collapsed"
)

# --- 4. LÓGICA DAS ABAS ---

if aba == "Estoque":
    df = buscar_dados("remedios")
    if not df.empty:
        hoje = datetime.now()
        for _, r in df.iterrows():
            # Cálculos de estoque originais do Rock
            ini = pd.to_datetime(r["data_inicio"])
            passados = (hoje - ini).days
            dose = float(r["dose_diaria"])
            atual = max(0.0, float(r["qtd_total"]) - (passados * dose))
            resta = float(atual / dose) if dose > 0 else 0
            data_fim = hoje + timedelta(days=resta)
            
            # Nova Lógica: Alerta baseado na coluna estoque_minimo
            minimo = r.get("estoque_minimo", 7)
            
            card_classe = ""
            if resta <= 3: card_classe = "medicine-critical"
            elif resta <= minimo: card_classe = "medicine-warning"

            st.markdown(f"""
                <div class="medicine-card {card_classe}">
                    <div class="medicine-name">
                        <div class="medicine-title">{escape(str(r['nome']))}</div>
                        <div style="font-size: 0.85em; color: #566573;">Fim: {data_fim.strftime('%d/%m/%Y')}</div>
                    </div>
                    <div class="medicine-pill">
                        <div class="medicine-label">Qtd</div>
                        <div class="medicine-value">{atual:g}</div>
                    </div>
                    <div class="medicine-pill">
                        <div class="medicine-label">Dias</div>
                        <div class="medicine-value">{int(resta)}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if st.session_state.autenticado:
                with st.expander("Ajustar Estoque"):
                    v_add = st.number_input("Qtd Comprada", 0.0, key=f"add_{r['id']}")
                    v_pago = st.number_input("Valor Pago R$", 0.0, key=f"pay_{r['id']}")
                    if st.button("Confirmar Compra", key=f"btn_{r['id']}", use_container_width=True):
                        # Atualiza estoque e gera registro financeiro automático
                        if requisicao_supabase("PATCH", f"remedios?id=eq.{r['id']}", "Erro", json={
                            "qtd_total": float(atual + v_add), "data_inicio": hoje.strftime("%Y-%m-%d"), "alerta_enviado": False
                        }):
                            requisicao_supabase("POST", "compras", "Erro", json={
                                "nome_remedio": r["nome"], "valor": float(v_pago), "data_compra": hoje.strftime("%Y-%m-%d")
                            })
                            st.cache_data.clear()
                            st.rerun()

elif aba == "Cadastrar":
    if st.session_state.autenticado:
        tipo = st.segmented_control("Tipo", ["Remédio", "Consulta"], default="Remédio")
        with st.form("cad_form"):
            if tipo == "Remédio":
                n = st.text_input("Nome do Remédio")
                col1, col2 = st.columns(2)
                q = col1.number_input("Quantidade Total", min_value=0.0)
                d = col2.number_input("Dose/Dia", min_value=0.0)
                p = col1.number_input("Preço de Custo (R$)", min_value=0.0)
                m = col2.number_input("Aviso Estoque Baixo (Dias)", min_value=1, value=5)
                
                if st.form_submit_button("Salvar no Sistema", use_container_width=True):
                    if n and q > 0:
                        # Cadastro completo com as NOVAS COLUNAS
                        if requisicao_supabase("POST", "remedios", "Erro", json={
                            "nome": n.strip(), "qtd_total": float(q), "dose_diaria": float(d),
                            "preco": float(p), "estoque_minimo": int(m),
                            "data_inicio": datetime.now().strftime("%Y-%m-%d"), "alerta_enviado": False
                        }):
                            # Já cria o registro financeiro na tabela de compras
                            requisicao_supabase("POST", "compras", "Erro", json={
                                "nome_remedio": n.strip(), "valor": float(p), "data_compra": datetime.now().strftime("%Y-%m-%d")
                            })
                            st.cache_data.clear()
                            st.success("✅ Remédio e Gasto cadastrados!")
                            st.rerun()
            else:
                # Cadastro de Consultas original
                med = st.text_input("Médico")
                val = st.number_input("Valor da Consulta")
                if st.form_submit_button("Salvar Consulta", use_container_width=True):
                    requisicao_supabase("POST", "consultas", "Erro", json={
                        "medico": med, "valor": float(val), "data_consulta": datetime.now().strftime("%Y-%m-%d")
                    })
                    st.cache_data.clear()
                    st.rerun()
    else:
        st.warning("Área Restrita. Faça login na lateral.")

elif aba == "Remover":
    if st.session_state.autenticado:
        tabela = st.selectbox("O que deseja remover?", ["remedios", "consultas", "compras"])
        dados = buscar_dados(tabela)
        if not dados.empty:
            col_nome = "nome" if tabela == "remedios" else ("nome_remedio" if tabela == "compras" else "medico")
            escolha = st.selectbox("Selecione o item", dados[col_nome].tolist())
            
            if st.button("EXCLUIR PERMANENTEMENTE", type="primary", use_container_width=True):
                id_item = dados[dados[col_nome] == escolha]["id"].values[0]
                
                # Deleta o item principal
                if requisicao_supabase("DELETE", f"{tabela}?id=eq.{id_item}", "Erro"):
                    # Se apagou um remédio, limpa também todo o histórico de compras dele (Financeiro)
                    if tabela == "remedios":
                        requisicao_supabase("DELETE", f"compras?nome_remedio=eq.{escolha}", "Erro")
                    
                    st.cache_data.clear()
                    st.success("Registro removido de todos os controles!")
                    st.rerun()
    else:
        st.warning("Área Restrita.")

# --- (Aqui o código continua com as funções de BI, Exportação CSV e Gráficos que o Rock já possui) ---
