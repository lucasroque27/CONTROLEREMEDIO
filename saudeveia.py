import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from html import escape

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
res = requests.post(
"https://api.telegram.org/bot8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM/sendMessage",
json={"chat_id": "5256921022", "text": msg},
timeout=5,
)
return res.status_code == 200
except Exception:
return False


def requisicao_supabase(metodo, tabela, erro_contexto, **kwargs):
try:
res = requests.request(
metodo,
f"{URL_BASE}{tabela}",
headers=HEADERS,
timeout=15,
**kwargs,
)
if 200 <= res.status_code < 300:
return True
st.error(f"{erro_contexto}. Código: {res.status_code}. Resposta: {res.text[:180]}")
return False
except Exception as exc:
st.error(f"{erro_contexto}. Detalhe: {exc}")
return False


def texto_normalizado(valor):
return str(valor or "").strip().casefold()


@st.cache_data(ttl=1)
def buscar_dados(tabela):
try:
res = requests.get(f"{URL_BASE}{tabela}?select=*", headers=HEADERS, timeout=10)
return pd.DataFrame(res.json()) if res.status_code == 200 else pd.DataFrame()
except Exception:
return pd.DataFrame()


def dataframe_para_csv(df):
return df.to_csv(index=False).encode("utf-8-sig")


def avisar_sucesso(mensagem):
st.session_state.mensagem_sucesso = mensagem


def mostrar_mensagem_sucesso():
mensagem = st.session_state.pop("mensagem_sucesso", None)
if mensagem:
st.success(mensagem)


def montar_gastos_unificados(df_com, df_con):
registros = []

if not df_com.empty:
compras = df_com.copy()
compras["data_compra"] = pd.to_datetime(compras["data_compra"], errors="coerce")
for _, item in compras.iterrows():
registros.append(
{
"data": item["data_compra"],
"mes_ano": "",
"tipo": "Remédio",
"descricao": item.get("nome_remedio", ""),
"valor": float(item.get("valor", 0) or 0),
"origem": "compras",
"id_origem": item.get("id", ""),
}
)

if not df_con.empty:
consultas = df_con.copy()
consultas["data_consulta"] = pd.to_datetime(consultas["data_consulta"], errors="coerce")
for _, item in consultas.iterrows():
registros.append(
{
"data": item["data_consulta"],
"mes_ano": "",
"tipo": "Consulta",
"descricao": item.get("medico", ""),
"valor": float(item.get("valor", 0) or 0),
"origem": "consultas",
"id_origem": item.get("id", ""),
}
)

colunas = ["data", "mes_ano", "tipo", "descricao", "valor", "origem", "id_origem"]
df_gastos = pd.DataFrame(registros, columns=colunas)
if not df_gastos.empty:
df_gastos = df_gastos.dropna(subset=["data"]).sort_values("data", ascending=False)
df_gastos["mes_ano"] = df_gastos["data"].dt.strftime("%Y-%m")
df_gastos["data"] = df_gastos["data"].dt.strftime("%Y-%m-%d")

return df_gastos


# --- 2. CONFIGURAÇÃO DE TELA E CSS ---
st.set_page_config(
page_title="Saúde Rock",
layout="centered",
initial_sidebar_state="collapsed",
)

PALETAS = {
"Clinico Azul": {
"bg": "#f7f9fc",
"card": "#ffffff",
"text": "#172033",
"muted": "#667085",
"border": "#d7dee8",
"accent": "#1d5f8f",
"accent_strong": "#164a73",
"soft": "#eef6fb",
"success": "#167c5a",
"success_bg": "#edf8f4",
"danger": "#b42318",
"danger_bg": "#fff1f0",
"warning": "#a15c07",
"warning_bg": "#fff7e8",
"header": "rgba(247, 249, 252, 0.94)",
},
"Coral Vivo": {
"bg": "#fff8f5",
"card": "#ffffff",
"text": "#211b1b",
"muted": "#746b66",
"border": "#eadbd4",
"accent": "#d9472f",
"accent_strong": "#a93624",
"soft": "#fff0ea",
"success": "#18715c",
"success_bg": "#ecf8f4",
"danger": "#b42318",
"danger_bg": "#fff1f0",
"warning": "#9a5b00",
"warning_bg": "#fff5df",
"header": "rgba(255, 248, 245, 0.94)",
},
"Verde Safira": {
"bg": "#f4fbfa",
"card": "#ffffff",
"text": "#102326",
"muted": "#5d7174",
"border": "#cfe4e2",
"accent": "#007f7a",
"accent_strong": "#005f5b",
"soft": "#e8f7f5",
"success": "#0f7a4f",
"success_bg": "#eaf8f1",
"danger": "#b42318",
"danger_bg": "#fff1f0",
"warning": "#9a6200",
"warning_bg": "#fff7e2",
"header": "rgba(244, 251, 250, 0.94)",
},
"Safira Impacto": {
"bg": "#f5f7ff",
"card": "#ffffff",
"text": "#121a35",
"muted": "#5f6882",
"border": "#d8def2",
"accent": "#3454d1",
"accent_strong": "#243a99",
"soft": "#eef1ff",
"success": "#14795b",
"success_bg": "#edf8f4",
"danger": "#b42318",
"danger_bg": "#fff1f0",
"warning": "#9b5b00",
"warning_bg": "#fff6e3",
"header": "rgba(245, 247, 255, 0.94)",
},
"Roxo Neon": {
"bg": "#fbf7ff",
"card": "#ffffff",
"text": "#20142f",
"muted": "#6f617d",
"border": "#e2d4ef",
"accent": "#7c3aed",
"accent_strong": "#5b21b6",
"soft": "#f3e8ff",
"success": "#10845f",
"success_bg": "#ebf9f3",
"danger": "#c02635",
"danger_bg": "#fff1f3",
"warning": "#a16207",
"warning_bg": "#fff7df",
"header": "rgba(251, 247, 255, 0.94)",
},
"Azul Eletrico": {
"bg": "#f3faff",
"card": "#ffffff",
"text": "#102033",
"muted": "#5d6d7d",
"border": "#cfe4f5",
"accent": "#0284c7",
"accent_strong": "#075985",
"soft": "#e7f5ff",
"success": "#087f5b",
"success_bg": "#eaf8f2",
"danger": "#b42318",
"danger_bg": "#fff1f0",
"warning": "#a15c07",
"warning_bg": "#fff6df",
"header": "rgba(243, 250, 255, 0.94)",
},
"Lima Energia": {
"bg": "#f8fff2",
"card": "#ffffff",
"text": "#18220f",
"muted": "#627052",
"border": "#d8e9c7",
"accent": "#65a30d",
"accent_strong": "#3f6212",
"soft": "#f0f9e4",
"success": "#15803d",
"success_bg": "#edf8ed",
"danger": "#b42318",
"danger_bg": "#fff1f0",
"warning": "#a15c07",
"warning_bg": "#fff7df",
"header": "rgba(248, 255, 242, 0.94)",
},
"Magenta Clinico": {
"bg": "#fff5fb",
"card": "#ffffff",
"text": "#2b1422",
"muted": "#765f6d",
"border": "#efd2e3",
"accent": "#db2777",
"accent_strong": "#9d174d",
"soft": "#fce7f3",
"success": "#0f7a5a",
"success_bg": "#ebf8f3",
"danger": "#b42318",
"danger_bg": "#fff1f0",
"warning": "#a15c07",
"warning_bg": "#fff7df",
"header": "rgba(255, 245, 251, 0.94)",
},
"Laranja Premium": {
"bg": "#fffaf2",
"card": "#ffffff",
"text": "#26190b",
"muted": "#735f48",
"border": "#ead9bd",
"accent": "#ea580c",
"accent_strong": "#9a3412",
"soft": "#ffedd5",
"success": "#157f55",
"success_bg": "#ecf8f2",
"danger": "#b42318",
"danger_bg": "#fff1f0",
"warning": "#92400e",
"warning_bg": "#fff7e8",
"header": "rgba(255, 250, 242, 0.94)",
},
"Ciano Futuro": {
"bg": "#f0fdff",
"card": "#ffffff",
"text": "#0f2530",
"muted": "#52717b",
"border": "#c5e8ee",
"accent": "#0891b2",
"accent_strong": "#155e75",
"soft": "#cffafe",
"success": "#0f766e",
"success_bg": "#e7f8f5",
"danger": "#b42318",
"danger_bg": "#fff1f0",
"warning": "#a15c07",
"warning_bg": "#fff7df",
"header": "rgba(240, 253, 255, 0.94)",
},
"Rosa Luxo": {
"bg": "#fff1f8",
"card": "#ffffff",
"text": "#301525",
"muted": "#7a6070",
"border": "#f0c7dc",
"accent": "#e11d74",
"accent_strong": "#9f1239",
"soft": "#fce7f3",
"success": "#0f766e",
"success_bg": "#e7f8f5",
"danger": "#be123c",
"danger_bg": "#fff1f2",
"warning": "#a16207",
"warning_bg": "#fff7df",
"header": "rgba(255, 241, 248, 0.94)",
},
"Lavanda Clara": {
"bg": "#fbf8ff",
"card": "#ffffff",
"text": "#241533",
"muted": "#70627d",
"border": "#e5d7f4",
"accent": "#8b5cf6",
"accent_strong": "#6d28d9",
"soft": "#f3edff",
"success": "#0f766e",
"success_bg": "#e7f8f5",
"danger": "#b42318",
"danger_bg": "#fff1f0",
"warning": "#9a6200",
"warning_bg": "#fff7e2",
"header": "rgba(251, 248, 255, 0.94)",
},
"Menta Leve": {
"bg": "#f3fff9",
"card": "#ffffff",
"text": "#10231b",
"muted": "#5b7066",
"border": "#ccebdc",
"accent": "#10b981",
"accent_strong": "#047857",
"soft": "#e7f8f0",
"success": "#0f7a4f",
"success_bg": "#e9f8f0",
"danger": "#b42318",
"danger_bg": "#fff1f0",
"warning": "#9a6200",
"warning_bg": "#fff7df",
"header": "rgba(243, 255, 249, 0.94)",
},
"Amarelo Solar": {
"bg": "#fffdf2",
"card": "#ffffff",
"text": "#261f0a",
"muted": "#746849",
"border": "#eadfba",
"accent": "#d97706",
"accent_strong": "#92400e",
"soft": "#fff7d6",
"success": "#157f55",
"success_bg": "#ecf8f2",
"danger": "#b42318",
"danger_bg": "#fff1f0",
"warning": "#a15c07",
"warning_bg": "#fff4cc",
"header": "rgba(255, 253, 242, 0.94)",
},
"Azul Gelo": {
"bg": "#f5fbff",
"card": "#ffffff",
"text": "#112236",
"muted": "#607489",
"border": "#d1e5f6",
"accent": "#2563eb",
"accent_strong": "#1d4ed8",
"soft": "#eaf4ff",
"success": "#0f766e",
"success_bg": "#e7f8f5",
"danger": "#b42318",
"danger_bg": "#fff1f0",
"warning": "#a15c07",
"warning_bg": "#fff7df",
"header": "rgba(245, 251, 255, 0.94)",
},
"Pessego Claro": {
"bg": "#fff7ed",
"card": "#ffffff",
"text": "#2b1a10",
"muted": "#765f50",
"border": "#efd7c3",
"accent": "#f97316",
"accent_strong": "#c2410c",
"soft": "#ffedd5",
"success": "#14795b",
"success_bg": "#edf8f4",
"danger": "#b42318",
"danger_bg": "#fff1f0",
"warning": "#92400e",
"warning_bg": "#fff7e8",
"header": "rgba(255, 247, 237, 0.94)",
},
"Turquesa Claro": {
"bg": "#f2fffd",
"card": "#ffffff",
"text": "#0f2927",
"muted": "#587572",
"border": "#c9e8e3",
"accent": "#14b8a6",
"accent_strong": "#0f766e",
"soft": "#e3faf6",
"success": "#0f7a5a",
"success_bg": "#ebf8f3",
"danger": "#b42318",
"danger_bg": "#fff1f0",
"warning": "#9a6200",
"warning_bg": "#fff7df",
"header": "rgba(242, 255, 253, 0.94)",
},
}

if "autenticado" not in st.session_state:
st.session_state.autenticado = False
if "tema_visual" not in st.session_state:
st.session_state.tema_visual = "Clinico Azul"
if st.session_state.tema_visual not in PALETAS:
st.session_state.tema_visual = "Clinico Azul"

paleta = PALETAS.get(st.session_state.tema_visual, PALETAS["Clinico Azul"])

st.markdown(
"""
   <style>
   :root {
       --saude-bg: #f7f9fc;
       --saude-card: #ffffff;
       --saude-text: #172033;
       --saude-muted: #667085;
       --saude-border: #d7dee8;
       --saude-accent: #1d5f8f;
       --saude-accent-strong: #164a73;
       --saude-soft: #eef6fb;
       --saude-success: #167c5a;
       --saude-success-bg: #edf8f4;
       --saude-danger: #b42318;
       --saude-danger-bg: #fff1f0;
       --saude-warning: #a15c07;
       --saude-warning-bg: #fff7e8;
   }

   html, body, [data-testid="stAppViewContainer"] {
       background: var(--saude-bg);
       color: var(--saude-text);
   }

   [data-testid="stHeader"] {
       background: rgba(247, 249, 252, 0.94);
       backdrop-filter: blur(8px);
       border-bottom: 1px solid rgba(215, 222, 232, .82);
   }

   div.block-container {
       max-width: 760px;
       padding-top: 2.75rem;
       padding-left: 1rem;
       padding-right: 1rem;
       padding-bottom: 2rem;
   }

   h1, h2, h3, h4, p, label, span {
       letter-spacing: 0;
   }

   .app-title {
       text-align: center;
       margin: .35rem 0 .25rem;
       font-size: clamp(1.35rem, 4vw, 1.75rem);
       line-height: 1.35;
       font-weight: 800;
       color: var(--saude-text);
       overflow: visible;
   }

   .app-subtitle {
       text-align: center;
       margin: 0 0 .9rem;
       color: var(--saude-muted);
       font-size: .9rem;
       line-height: 1.35;
   }

   [data-testid="stSidebar"] {
       background: var(--saude-card);
       border-right: 1px solid var(--saude-border);
   }

   [data-testid="stSidebar"] * {
       color: var(--saude-text);
   }

   div[data-testid="stSegmentedControl"] {
       margin-bottom: .95rem;
   }

   div[data-testid="stSegmentedControl"] div[role="radiogroup"] {
       display: flex;
       flex-wrap: nowrap;
       gap: 0;
       overflow-x: auto;
       padding: .18rem;
       scrollbar-width: thin;
       border: 1px solid var(--saude-border);
       border-radius: 7px;
       background: color-mix(in srgb, var(--saude-soft) 55%, #ffffff);
   }

   div[data-testid="stSegmentedControl"] label {
       min-height: 2.15rem;
       border-radius: 5px;
       white-space: nowrap;
       font-weight: 650;
       flex: 0 0 auto;
       border: 1px solid transparent !important;
       background: transparent !important;
       color: var(--saude-text) !important;
   }

   div[data-testid="stSegmentedControl"] label * {
       color: var(--saude-text) !important;
   }

   div[data-testid="stSegmentedControl"] label:hover {
       border-color: var(--saude-accent) !important;
       background: var(--saude-card) !important;
   }

   div[data-testid="stSegmentedControl"] label:has(input:checked) {
       border-color: var(--saude-accent) !important;
       background: var(--saude-accent) !important;
   }

   div[data-testid="stSegmentedControl"] label:has(input:checked) * {
       color: #ffffff !important;
   }

   div[data-testid="stVerticalBlockBorderWrapper"] {
       border: 1px solid var(--saude-border);
       border-radius: 7px;
       background: var(--saude-card);
       box-shadow: 0 4px 14px rgba(23, 32, 51, 0.035);
       margin-bottom: .48rem;
   }

   .medicine-card {
       display: grid;
       grid-template-columns: minmax(0, 1.55fr) repeat(3, minmax(58px, .55fr));
       gap: .38rem;
       align-items: stretch;
       width: 100%;
       border-left: 3px solid var(--saude-accent);
       padding-left: .5rem;
   }

   .medicine-name {
       min-width: 0;
       display: flex;
       flex-direction: column;
       justify-content: center;
       gap: .15rem;
   }

   .medicine-title {
       font-weight: 780;
       font-size: .94rem;
       color: var(--saude-text);
       line-height: 1.2;
       overflow-wrap: anywhere;
   }

   .medicine-date {
       color: var(--saude-muted);
       font-size: .74rem;
       line-height: 1.2;
   }

   .medicine-status {
       display: inline-flex;
       align-items: center;
       width: fit-content;
       max-width: 100%;
       margin-bottom: .12rem;
       padding: .12rem .38rem;
       border-radius: 999px;
       border: 1px solid var(--saude-border);
       background: var(--saude-soft);
       color: var(--saude-accent-strong);
       font-size: .64rem;
       font-weight: 760;
       line-height: 1.1;
   }

   .medicine-pill {
       border: 1px solid var(--saude-border);
       border-radius: 6px;
       background: var(--saude-soft);
       padding: .36rem .4rem;
       min-width: 0;
   }

   .medicine-label {
       color: var(--saude-muted);
       font-size: .68rem;
       line-height: 1.05;
       margin-bottom: .18rem;
   }

   .medicine-value {
       color: var(--saude-text);
       font-weight: 760;
       font-size: .98rem;
       line-height: 1.05;
       overflow-wrap: anywhere;
   }

   .medicine-warning {
       border-left-color: var(--saude-warning);
   }

   .medicine-warning .medicine-pill:last-child {
       background: var(--saude-warning-bg);
       border-color: #f4d7a1;
   }

   .medicine-warning .medicine-pill:last-child .medicine-value,
   .medicine-warning .medicine-date {
       color: var(--saude-warning);
   }

   .medicine-warning .medicine-status {
       border-color: #f4d7a1;
       background: var(--saude-warning-bg);
       color: var(--saude-warning);
   }

   .medicine-critical {
       border-left-color: var(--saude-danger);
   }

   .medicine-critical .medicine-pill:last-child {
       background: var(--saude-danger-bg);
       border-color: #f3b8b3;
   }

   .medicine-critical .medicine-pill:last-child .medicine-value {
       color: var(--saude-danger);
   }

   .medicine-critical .medicine-status {
       border-color: #f3b8b3;
       background: var(--saude-danger-bg);
       color: var(--saude-danger);
   }

   .medicine-empty {
       color: var(--saude-danger);
       font-weight: 760;
   }

   div[data-testid="stMetric"] {
       background: var(--saude-soft);
       border: 1px solid var(--saude-border);
       border-radius: 6px;
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
       border-radius: 7px;
       overflow: hidden;
   }

   input, textarea, select {
       color: var(--saude-text) !important;
   }

   div.stButton > button,
   div.stDownloadButton > button,
   div[data-testid="stFormSubmitButton"] > button {
       border-radius: 8px;
       min-height: 2.55rem;
       font-weight: 650;
       border-color: var(--saude-border);
       background: var(--saude-card);
       color: var(--saude-text);
       box-shadow: none;
   }

   div.stButton > button[kind="primary"] {
       background: var(--saude-accent);
       border-color: var(--saude-accent);
   }

   div.stButton > button:hover,
   div.stDownloadButton > button:hover,
   div[data-testid="stFormSubmitButton"] > button:hover {
       border-color: var(--saude-accent);
       color: var(--saude-accent-strong);
   }

   .stAlert {
       border-radius: 7px;
   }

   @media (max-width: 640px) {
       div.block-container {
           padding-top: 3.25rem;
           padding-left: .65rem;
           padding-right: .65rem;
       }

       .app-title {
           font-size: 1.35rem;
           margin-top: .5rem;
           line-height: 1.4;
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

       .medicine-card {
           grid-template-columns: minmax(86px, 1.35fr) repeat(3, minmax(52px, .7fr));
           gap: .35rem;
           padding-left: .45rem;
       }

       .medicine-title {
           font-size: .82rem;
       }

       .medicine-date {
           font-size: .68rem;
       }

       .medicine-status {
           font-size: .58rem;
           padding: .1rem .3rem;
       }

       .medicine-pill {
           padding: .32rem .32rem;
       }

       .medicine-label {
           font-size: .62rem;
       }

       .medicine-value {
           font-size: .88rem;
       }
   }
   </style>
   """,
unsafe_allow_html=True,
)

st.markdown(
f"""
   <style>
   :root {{
       --saude-bg: {paleta["bg"]};
       --saude-card: {paleta["card"]};
       --saude-text: {paleta["text"]};
       --saude-muted: {paleta["muted"]};
       --saude-border: {paleta["border"]};
       --saude-accent: {paleta["accent"]};
       --saude-accent-strong: {paleta["accent_strong"]};
       --saude-soft: {paleta["soft"]};
       --saude-success: {paleta["success"]};
       --saude-success-bg: {paleta["success_bg"]};
       --saude-danger: {paleta["danger"]};
       --saude-danger-bg: {paleta["danger_bg"]};
       --saude-warning: {paleta["warning"]};
       --saude-warning-bg: {paleta["warning_bg"]};
   }}

   [data-testid="stHeader"] {{
       background: {paleta["header"]};
   }}

   .app-title::before {{
       content: "+";
       display: inline-flex;
       align-items: center;
       justify-content: center;
       width: 1.35rem;
       height: 1.35rem;
       margin-right: .45rem;
       border-radius: 6px;
       background: var(--saude-accent);
       color: #ffffff;
       font-size: 1rem;
       line-height: 1;
       vertical-align: .08rem;
   }}
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
    st.title("🔒 Controle medicamentos")
    st.title("🔒 ADM")
if not st.session_state.autenticado:
senha = st.text_input("Senha", type="password")
if st.button("Entrar") or senha == "1234":
if senha == "1234":
st.session_state.autenticado = True
st.rerun()
else:
st.selectbox("Tema visual", list(PALETAS.keys()), key="tema_visual")
if st.button("Sair"):
st.session_state.autenticado = False
st.rerun()

# Menu Superior Compacto
st.markdown("<h3 class='app-title'>MEDICAMENTOS DA VEIA</h3>", unsafe_allow_html=True)
st.markdown("<h3 class='app-title'>Minha Saúde</h3>", unsafe_allow_html=True)
st.markdown("<p class='app-subtitle'>Controle de remédios, consultas e gastos</p>", unsafe_allow_html=True)
aba = st.segmented_control(
"Menu",
options=["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"],
default="Estoque",
label_visibility="collapsed",
)
mostrar_mensagem_sucesso()

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
alerta_ja_enviado = bool(r.get("alerta_enviado", False))

# Alerta Telegram
if (
0 < resta <= 7
and not alerta_ja_enviado
and r["id"] not in st.session_state.alertas_enviados
):
telegram_ok = enviar_telegram(f"⚠️ {r['nome']} acaba em {int(resta)} dias!")
st.session_state.alertas_enviados.append(r["id"])
if telegram_ok:
requisicao_supabase(
"PATCH",
f"remedios?id=eq.{r['id']}",
"Alerta enviado, mas não foi possível marcar como enviado no banco",
json={"alerta_enviado": True},
)
st.cache_data.clear()
else:
st.warning(f"Não foi possível enviar o alerta do Telegram para {r['nome']}.")

with st.container(border=True):
if dose <= 0:
status_nome = "Dose inválida"
status_texto = ""
status_classe = "medicine-empty"
card_classe = "medicine-critical"
elif resta > 0:
if resta <= 3:
status_nome = "Crítico"
card_classe = "medicine-critical"
status_classe = "medicine-empty"
elif resta <= 7:
status_nome = "Atenção"
card_classe = "medicine-warning"
status_classe = ""
else:
status_nome = "Normal"
card_classe = ""
status_classe = ""
status_texto = f"Término: {data_fim.strftime('%d/%m/%Y')}"
else:
status_nome = "Zerado"
status_texto = "Estoque zerado"
status_classe = "medicine-empty"
card_classe = "medicine-critical"

st.markdown(
f"""
                   <div class="medicine-card {card_classe}">
                       <div class="medicine-name">
                           <div class="medicine-title">{escape(str(r['nome']).upper())}</div>
                           <div class="medicine-status">{status_nome}</div>
                           <div class="medicine-date {status_classe}">{status_texto}</div>
                       </div>
                       <div class="medicine-pill">
                           <div class="medicine-label">Qtd</div>
                           <div class="medicine-value">{atual:g}</div>
                       </div>
                       <div class="medicine-pill">
                           <div class="medicine-label">Dose</div>
                           <div class="medicine-value">{dose:g}</div>
                       </div>
                       <div class="medicine-pill">
                           <div class="medicine-label">Dias</div>
                           <div class="medicine-value">{int(resta)}</div>
                       </div>
                   </div>
                   """,
unsafe_allow_html=True,
)

if dose <= 0:
st.warning("Dose diária precisa ser maior que zero.")
elif resta <= 0:
st.error("Estoque Zerado")

if st.session_state.autenticado:
with st.expander("Ajustar Estoque"):
v_add = st.number_input("Qtd Comprada", 0.0, key=f"a_{r['id']}")
v_pago = st.number_input("Valor Pago R$", 0.0, key=f"p_{r['id']}")
if st.button("Salvar Registro", key=f"b_{r['id']}", use_container_width=True):
if v_add <= 0:
st.error("Informe uma quantidade comprada maior que zero.")
st.stop()
if v_pago < 0:
st.error("O valor pago não pode ser negativo.")
st.stop()

ok_estoque = requisicao_supabase(
"PATCH",
f"remedios?id=eq.{r['id']}",
"Não foi possível atualizar o estoque",
json={
"qtd_total": float(atual + v_add),
"data_inicio": hoje.strftime("%Y-%m-%d"),
"alerta_enviado": False,
},
)
if not ok_estoque:
st.stop()

ok_compra = requisicao_supabase(
"POST",
"compras",
"Estoque atualizado, mas não foi possível registrar a compra",
json={
"nome_remedio": r["nome"],
"valor": float(v_pago),
"data_compra": hoje.strftime("%Y-%m-%d"),
},
)
if not ok_compra:
st.stop()

telegram_ok = enviar_telegram(
"✅ Estoque atualizado\n"
f"Remédio: {r['nome']}\n"
f"Qtd comprada: {v_add:g}\n"
f"Estoque atual: {atual + v_add:g}\n"
f"Dias estimados: {int((atual + v_add) / dose) if dose > 0 else 0}\n"
f"Valor pago: R$ {v_pago:,.2f}"
)
if not telegram_ok:
st.warning("Estoque salvo, mas não foi possível enviar o alerta no Telegram.")
st.cache_data.clear()
avisar_sucesso("Estoque atualizado com sucesso.")
st.rerun()
else:
st.info("Nenhum remédio cadastrado ainda.")

elif aba == "Financeiro":
st.subheader("💰 Gastos Mensais")
df_com = buscar_dados("compras")
df_con = buscar_dados("consultas")
df_gastos = montar_gastos_unificados(df_com, df_con)

col_a, col_m = st.columns(2)
ano_sel = col_a.selectbox("Ano", [2025, 2026], index=1)
mes_sel = col_m.selectbox("Mês", list(range(1, 13)), index=datetime.now().month - 1)

total_r = 0.0
total_c = 0.0
filtro_mes = pd.DataFrame()

if not df_gastos.empty:
datas_gastos = pd.to_datetime(df_gastos["data"], errors="coerce")
filtro_mes = df_gastos[
(datas_gastos.dt.year == ano_sel)
& (datas_gastos.dt.month == mes_sel)
].copy()

total_r = filtro_mes.loc[filtro_mes["tipo"] == "Remédio", "valor"].sum()
total_c = filtro_mes.loc[filtro_mes["tipo"] == "Consulta", "valor"].sum()

if not filtro_mes.empty:
st.write("**Detalhamento unificado:**")
st.dataframe(
filtro_mes[["data", "mes_ano", "tipo", "descricao", "valor"]],
hide_index=True,
use_container_width=True,
)
else:
st.info("Nenhum gasto encontrado para esse mês.")

st.divider()
st.metric("TOTAL INVESTIDO", f"R$ {total_r + total_c:,.2f}")
st.info(f"Remédios: R$ {total_r:,.2f} | Consultas: R$ {total_c:,.2f}")
if not df_gastos.empty:
st.download_button(
"Baixar planilha unificada",
data=dataframe_para_csv(df_gastos),
file_name="gastos_unificados_power_bi.csv",
mime="text/csv",
use_container_width=True,
)
else:
st.info("Ainda não há dados financeiros para baixar.")

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
nome_limpo = n.strip()
if not nome_limpo:
st.error("Informe o nome do remédio.")
st.stop()
if q <= 0:
st.error("Informe uma quantidade maior que zero.")
st.stop()
if d <= 0:
st.error("Informe uma dose por dia maior que zero.")
st.stop()
if p < 0:
st.error("O preço não pode ser negativo.")
st.stop()

df_remedios = buscar_dados("remedios")
if not df_remedios.empty and "nome" in df_remedios:
nomes_existentes = df_remedios["nome"].map(texto_normalizado)
if texto_normalizado(nome_limpo) in set(nomes_existentes):
st.error("Já existe um remédio cadastrado com esse nome.")
st.stop()

ok_remedio = requisicao_supabase(
"POST",
"remedios",
"Não foi possível cadastrar o remédio",
json={
"nome": nome_limpo,
"qtd_total": float(q),
"dose_diaria": float(d),
"data_inicio": datetime.now().strftime("%Y-%m-%d"),
"alerta_enviado": False,
},
)
if not ok_remedio:
st.stop()

ok_compra = requisicao_supabase(
"POST",
"compras",
"Remédio cadastrado, mas não foi possível registrar a compra",
json={
"nome_remedio": nome_limpo,
"valor": float(p),
"data_compra": datetime.now().strftime("%Y-%m-%d"),
},
)
if not ok_compra:
st.stop()
st.cache_data.clear()
avisar_sucesso("Remédio cadastrado com sucesso.")
st.rerun()
else:
m = st.text_input("Médico")
v = st.number_input("Valor")
if st.form_submit_button("Salvar", use_container_width=True):
medico_limpo = m.strip()
hoje_str = datetime.now().strftime("%Y-%m-%d")
if not medico_limpo:
st.error("Informe o médico ou descrição da consulta.")
st.stop()
if v <= 0:
st.error("Informe um valor maior que zero.")
st.stop()

df_consultas = buscar_dados("consultas")
if not df_consultas.empty:
consultas = df_consultas.copy()
consultas["data_consulta"] = pd.to_datetime(
consultas["data_consulta"], errors="coerce"
).dt.strftime("%Y-%m-%d")
consultas["valor"] = pd.to_numeric(consultas["valor"], errors="coerce")
duplicada = consultas[
(consultas["medico"].map(texto_normalizado) == texto_normalizado(medico_limpo))
& (consultas["data_consulta"] == hoje_str)
& (consultas["valor"] == float(v))
]
if not duplicada.empty:
st.error("Essa consulta já foi cadastrada hoje com o mesmo valor.")
st.stop()

ok_consulta = requisicao_supabase(
"POST",
"consultas",
"Não foi possível cadastrar a consulta",
json={
"medico": medico_limpo,
"valor": float(v),
"data_consulta": hoje_str,
},
)
if not ok_consulta:
st.stop()
st.cache_data.clear()
avisar_sucesso("Consulta cadastrada com sucesso.")
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
if st.button("Apagar registro", type="primary", use_container_width=True):
id_i = df_del[df_del[c] == item]["id"].values[0]
ok_delete = requisicao_supabase(
"DELETE",
f"{tab}?id=eq.{id_i}",
"Não foi possível remover o item",
)
if not ok_delete:
st.stop()
if tab == "remedios":
ok_compras = requisicao_supabase(
"DELETE",
f"compras?nome_remedio=eq.{item}",
"Remédio removido, mas não foi possível remover as compras relacionadas",
)
if not ok_compras:
st.stop()
st.cache_data.clear()
avisar_sucesso("Item removido com sucesso.")
st.rerun()
else:
st.info("Não há itens para remover nessa tabela.")
else:
st.warning("Acesse o menu ADM na lateral.")
