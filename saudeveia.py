
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
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}


def enviar_telegram(msg):
    try:
        requests.post(
            "https://api.telegram.org/bot8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM/sendMessage",
            json={"chat_id": "5256921022", "text": msg},
            timeout=5,
        )
    except Exception:
        pass


@st.cache_data(ttl=1)
def buscar_dados(tabela):
    try:
        res = requests.get(f"{URL_BASE}{tabela}?select=*", headers=HEADERS, timeout=10)
        return pd.DataFrame(res.json()) if res.status_code == 200 else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def dataframe_para_csv(df):
    return df.to_csv(index=False).encode("utf-8-sig")


# --- 2. CONFIGURAÇÃO DE TELA E CSS ---
st.set_page_config(
    page_title="Saúde Rock",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --saude-bg: #f6f8fb;
        --saude-card: #ffffff;
        --saude-text: #18202f;
        --saude-muted: #5c6678;
        --saude-border: #dfe5ef;
        --saude-accent: #1976d2;
        --saude-soft: #eef5ff;
        --saude-danger: #b42318;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background: var(--saude-bg);
        color: var(--saude-text);
    }

    [data-testid="stHeader"] {
        background: rgba(246, 248, 251, 0.92);
        backdrop-filter: blur(8px);
    }

    div.block-container {
        max-width: 760px;
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3, h4, p, label, span {
        letter-spacing: 0;
    }

    .app-title {
        text-align: center;
        margin: 0 0 .15rem;
        font-size: clamp(1.35rem, 4vw, 1.75rem);
        font-weight: 800;
        color: var(--saude-text);
    }

    .app-subtitle {
        text-align: center;
        margin: 0 0 1rem;
        color: var(--saude-muted);
        font-size: .9rem;
    }

    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--saude-border);
    }

    div[data-testid="stSelectSlider"] {
        margin-bottom: .75rem;
    }

    div[data-testid="stSelectSlider"] > div {
        overflow-x: auto;
        padding-bottom: .15rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid var(--saude-border);
        border-radius: 10px;
        background: var(--saude-card);
        box-shadow: 0 10px 28px rgba(24, 32, 47, 0.06);
    }

    div[data-testid="stMetric"] {
        background: var(--saude-soft);
        border: 1px solid #d8e8ff;
        border-radius: 8px;
        padding: .65rem .7rem;
        min-height: 86px;
    }

    div[data-testid="stMetric"] label {
        color: var(--saude-muted);
        font-size: .82rem;
        line-height: 1.15;
    }

    div[data-testid="stMetricValue"] {
        font-size: clamp(1.15rem, 6vw, 1.75rem);
        line-height: 1.1;
        color: var(--saude-text);
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--saude-border);
        border-radius: 8px;
        overflow: hidden;
    }

    div.stButton > button,
    div.stDownloadButton > button,
    div[data-testid="stFormSubmitButton"] > button {
        border-radius: 8px;
        min-height: 2.75rem;
        font-weight: 700;
    }

    .stAlert {
        border-radius: 8px;
    }

    @media (max-width: 640px) {
        div.block-container {
            padding-top: .65rem;
            padding-left: .75rem;
            padding-right: .75rem;
        }

        .app-title {
            font-size: 1.35rem;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: .45rem;
        }

        div[data-testid="column"] {
            min-width: 0 !important;
        }

        div[data-testid="stMetric"] {
            padding: .55rem .45rem;
            min-height: 78px;
        }

        div[data-testid="stMetric"] label {
            font-size: .76rem;
            white-space: normal;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.18rem;
        }

        [data-testid="stExpander"] details {
            border-radius: 8px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "alertas_enviados" not in st.session_state:
    st.session_state.alertas_enviados = []

# Menu Lateral (Login)
with st.sidebar:
    st.title("🔒 ADM")
    if not st.session_state.autenticado:
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar") or senha == "1234":
            if senha == "1234":
                st.session_state.autenticado = True
                st.rerun()
    else:
        if st.button("Sair"):
            st.session_state.autenticado = False
            st.rerun()

# Menu Superior Compacto
st.markdown("<h3 class='app-title'>🏥 Minha Saúde</h3>", unsafe_allow_html=True)
st.markdown("<p class='app-subtitle'>Controle de remédios, consultas e gastos</p>", unsafe_allow_html=True)
aba = st.select_slider(
    "",
    options=["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"],
    label_visibility="collapsed",
)

# --- 3. TELAS ---

if aba == "Estoque":
    df = buscar_dados("remedios")
    if not df.empty:
        hoje = datetime.now()
        for _, r in df.iterrows():
            ini = pd.to_datetime(r["data_inicio"])
            passados = (hoje - ini).days
            dose = float(r["dose_diaria"])
            atual = max(0.0, float(r["qtd_total"]) - (passados * dose))
            resta = float(atual / dose) if dose > 0 else 0
            data_fim = hoje + timedelta(days=resta)

            # Alerta Telegram
            if 0 < resta <= 7 and r["id"] not in st.session_state.alertas_enviados:
                enviar_telegram(f"⚠️ {r['nome']} acaba em {int(resta)} dias!")
                st.session_state.alertas_enviados.append(r["id"])

            with st.container(border=True):
                st.markdown(f"**{str(r['nome']).upper()}**")
                c1, c2, c3 = st.columns(3)
                c1.metric("Qtd", f"{atual:g}")
                c2.metric("Dose", f"{dose:g}")
                c3.metric("Dias", int(resta))

                if dose <= 0:
                    st.warning("Dose diária precisa ser maior que zero.")
                elif resta > 0:
                    st.caption(f"📅 Término: {data_fim.strftime('%d/%m/%Y')}")
                else:
                    st.error("Estoque Zerado")

                if st.session_state.autenticado:
                    with st.expander("Ajustar Estoque"):
                        v_add = st.number_input("Qtd Comprada", 0.0, key=f"a_{r['id']}")
                        v_pago = st.number_input("Valor Pago R$", 0.0, key=f"p_{r['id']}")
                        if st.button("Salvar Registro", key=f"b_{r['id']}", use_container_width=True):
                            requests.patch(
                                f"{URL_BASE}remedios?id=eq.{r['id']}",
                                headers=HEADERS,
                                json={
                                    "qtd_total": float(atual + v_add),
                                    "data_inicio": hoje.strftime("%Y-%m-%d"),
                                },
                            )
                            requests.post(
                                f"{URL_BASE}compras",
                                headers=HEADERS,
                                json={
                                    "nome_remedio": r["nome"],
                                    "valor": float(v_pago),
                                    "data_compra": hoje.strftime("%Y-%m-%d"),
                                },
                            )
                            st.cache_data.clear()
                            st.success("Ok!")
                            time.sleep(1)
                            st.rerun()
    else:
        st.info("Nenhum remédio cadastrado ainda.")

elif aba == "Financeiro":
    st.subheader("💰 Gastos Mensais")
    df_com = buscar_dados("compras")
    df_con = buscar_dados("consultas")

    col_a, col_m = st.columns(2)
    ano_sel = col_a.selectbox("Ano", [2025, 2026], index=1)
    mes_sel = col_m.selectbox("Mês", list(range(1, 13)), index=datetime.now().month - 1)

    total_r = 0.0
    total_c = 0.0

    if not df_com.empty:
        df_com["data_compra"] = pd.to_datetime(df_com["data_compra"])
        filtro_r = df_com[
            (df_com["data_compra"].dt.year == ano_sel)
            & (df_com["data_compra"].dt.month == mes_sel)
        ]
        total_r = filtro_r["valor"].sum()
        if not filtro_r.empty:
            st.write("**Detalhamento Remédios:**")
            st.dataframe(
                filtro_r[["nome_remedio", "valor", "data_compra"]],
                hide_index=True,
                use_container_width=True,
            )

    if not df_con.empty:
        df_con["data_consulta"] = pd.to_datetime(df_con["data_consulta"])
        filtro_c = df_con[
            (df_con["data_consulta"].dt.year == ano_sel)
            & (df_con["data_consulta"].dt.month == mes_sel)
        ]
        total_c = filtro_c["valor"].sum()

    st.divider()
    st.metric("TOTAL INVESTIDO", f"R$ {total_r + total_c:,.2f}")
    st.info(f"Remédios: R$ {total_r:,.2f} | Consultas: R$ {total_c:,.2f}")

elif aba == "Consultas":
    df = buscar_dados("consultas")
    if not df.empty:
        colunas_consulta = ["data_consulta", "medico", "valor"]
        df_consultas = df[colunas_consulta].copy()
        st.dataframe(df_consultas, hide_index=True, use_container_width=True)
        st.download_button(
            "Baixar planilha de consultas",
            data=dataframe_para_csv(df_consultas),
            file_name="consultas.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("Nenhuma consulta cadastrada ainda.")

elif aba == "Cadastrar":
    if st.session_state.autenticado:
        tipo = st.segmented_control("Tipo", ["Remédio", "Consulta"], default="Remédio")
        with st.form("cad"):
            if tipo == "Remédio":
                n = st.text_input("Nome")
                q = st.number_input("Qtd")
                d = st.number_input("Dose/Dia")
                p = st.number_input("Preço")
                if st.form_submit_button("Salvar", use_container_width=True):
                    requests.post(
                        f"{URL_BASE}remedios",
                        headers=HEADERS,
                        json={
                            "nome": n,
                            "qtd_total": float(q),
                            "dose_diaria": float(d),
                            "data_inicio": datetime.now().strftime("%Y-%m-%d"),
                        },
                    )
                    requests.post(
                        f"{URL_BASE}compras",
                        headers=HEADERS,
                        json={
                            "nome_remedio": n,
                            "valor": float(p),
                            "data_compra": datetime.now().strftime("%Y-%m-%d"),
                        },
                    )
                    st.cache_data.clear()
                    st.rerun()
            else:
                m = st.text_input("Médico")
                v = st.number_input("Valor")
                if st.form_submit_button("Salvar", use_container_width=True):
                    requests.post(
                        f"{URL_BASE}consultas",
                        headers=HEADERS,
                        json={
                            "medico": m,
                            "valor": float(v),
                            "data_consulta": datetime.now().strftime("%Y-%m-%d"),
                        },
                    )
                    st.cache_data.clear()
                    st.rerun()
    else:
        st.warning("Acesse o menu ADM na lateral.")

elif aba == "Remover":
    if st.session_state.autenticado:
        tab = st.selectbox("Tabela", ["remedios", "consultas", "compras"])
        df_del = buscar_dados(tab)
        if not df_del.empty:
            c = "nome" if tab == "remedios" else ("nome_remedio" if tab == "compras" else "medico")
            item = st.selectbox("Item", df_del[c].tolist())
            if st.button("🗑️ APAGAR", type="primary", use_container_width=True):
                id_i = df_del[df_del[c] == item]["id"].values[0]
                requests.delete(f"{URL_BASE}{tab}?id=eq.{id_i}", headers=HEADERS)
                if tab == "remedios":
                    requests.delete(f"{URL_BASE}compras?nome_remedio=eq.{item}", headers=HEADERS)
                st.cache_data.clear()
                st.rerun()
        else:
            st.info("Não há itens para remover nessa tabela.")
    else:
        st.warning("Acesse o menu ADM na lateral.")
