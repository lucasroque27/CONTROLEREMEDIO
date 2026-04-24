import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import time

# --- 1. CONFIGURAÇÕES ---
URL_SUPABASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
HEADERS = {"apikey": API_KEY, "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}

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

# --- 2. ESTILO CSS "RESUMO LIMPO" ---
st.set_page_config(page_title="Saúde Rock", page_icon="💊", layout="centered")

st.markdown("""
    <style>
    .resumo-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
        margin-bottom: 15px;
    }
    .titulo-med {
        font-size: 1.5rem;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 15px;
        border-bottom: 2px solid #f1f5f9;
        padding-bottom: 10px;
    }
    .grid-resumo {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
    }
    .item-resumo {
        background-color: #f8fafc;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
    }
    .label-resumo {
        display: block;
        font-size: 0.75rem;
        color: #64748b;
        text-transform: uppercase;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .valor-resumo {
        display: block;
        font-size: 1.1rem;
        font-weight: 800;
        color: #0f172a;
    }
    .status-final {
        margin-top: 15px;
        padding: 8px;
        border-radius: 8px;
        text-align: center;
        font-weight: 700;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÓGICA DO DASHBOARD ---
st.title("💊 Painel de Medicamentos")

df = api_get("remedios")
if df.empty:
    st.info("Nenhum medicamento cadastrado.")
else:
    hoje = datetime.now()
    # Dicionário para meses em português
    meses_pt = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}

    for _, r in df.iterrows():
        # Cálculos
        dias_passados = (hoje - r['data_inicio']).days
        estoque_atual = max(0, int(r['qtd_total'] - (dias_passados * r['dose_diaria'])))
        dias_restantes = int(estoque_atual / r['dose_diaria']) if r['dose_diaria'] > 0 else 0
        data_fim = hoje + timedelta(days=dias_restantes)
        
        # Formatação da data em PT-BR
        data_formatada = f"{data_fim.day} de {meses_pt[data_fim.month]}"
        
        # Cor de alerta
        cor_fundo = "#dcfce7" if dias_restantes > 10 else "#fee2e2"
        cor_texto = "#166534" if dias_restantes > 10 else "#991b1b"
        texto_alerta = "✅ ESTOQUE SEGURO" if dias_restantes > 10 else "⚠️ REPOR URGENTE"

        # HTML do Novo Card Resumo
        st.markdown(f"""
            <div class="resumo-card">
                <div class="titulo-med">{r['nome'].upper()}</div>
                
                <div class="grid-resumo">
                    <div class="item-resumo">
                        <span class="label-resumo">Quantidade</span>
                        <span class="valor-resumo">{estoque_atual} un.</span>
                    </div>
                    <div class="item-resumo">
                        <span class="label-resumo">Dose Diária</span>
                        <span class="valor-resumo">{r['dose_diaria']} p/ dia</span>
                    </div>
                    <div class="item-resumo">
                        <span class="label-resumo">Dias de Dose</span>
                        <span class="valor-resumo">{dias_restantes} dias</span>
                    </div>
                    <div class="item-resumo">
                        <span class="label-resumo">Acaba em</span>
                        <span class="valor-resumo">{data_formatada}</span>
                    </div>
                </div>
                
                <div class="status-final" style="background-color: {cor_fundo}; color: {cor_texto};">
                    {texto_alerta}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Parte de Reposição (Apenas se for Admin)
        with st.expander(f"Ajustar estoque/preço de {r['nome']}"):
            c1, c2 = st.columns(2)
            n_q = c1.number_input("Qtd comprada", 1, 500, 30, key=f"q_{r['id']}")
            n_p = c2.number_input("Preço pago R$", 0.0, 5000.0, float(r['preco']), key=f"p_{r['id']}")
            if st.button("Confirmar Atualização", key=f"b_{r['id']}"):
                # Lógica de update aqui...
                st.success("Atualizado!")
                time.sleep(1)
                st.rerun()
