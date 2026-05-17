from datetime import datetime
from html import escape

import pandas as pd
import requests
import streamlit as stfrom datetime import datetime, timedelta
from html import escape

import pandas as pd
import requests
import streamlit as st

try:
    import saude_core as core
except ModuleNotFoundError:
    class _CoreFallback:
        TABELA_REMEDIOS = "remedios"
        TABELA_COMPRAS = "compras"
        TABELA_CONSULTAS = "consultas"

        COL_ID = "id"
        COL_NOME = "nome"
        COL_QTD_TOTAL = "qtd_total"
        COL_DOSE_DIARIA = "dose_diaria"
        COL_DATA_INICIO = "data_inicio"
        COL_ALERTA_ENVIADO = "alerta_enviado"
        COL_NOME_REMEDIO = "nome_remedio"
        COL_VALOR = "valor"
        COL_DATA_COMPRA = "data_compra"
        COL_MEDICO = "medico"
        COL_DATA_CONSULTA = "data_consulta"

        TIPO_REMEDIO = "Remedio"
        TIPO_CONSULTA = "Consulta"

        COLUNAS_GASTOS = ["data", "mes_ano", "tipo", "descricao", "valor", "origem", "id_origem"]
        COLUNAS_GASTOS_VISIVEIS = ["data", "mes_ano", "tipo", "descricao", "valor"]
        COLUNAS_CONSULTA_VISIVEIS = [COL_DATA_CONSULTA, COL_MEDICO, COL_VALOR]

        MESES = {
            1: "Janeiro",
            2: "Fevereiro",
            3: "Marco",
            4: "Abril",
            5: "Maio",
            6: "Junho",
            7: "Julho",
            8: "Agosto",
            9: "Setembro",
            10: "Outubro",
            11: "Novembro",
            12: "Dezembro",
        }

        @staticmethod
        def texto_normalizado(valor):
            return str(valor or "").strip().casefold()

        @staticmethod
        def data_iso(data_valor):
            return pd.to_datetime(data_valor).strftime("%Y-%m-%d")

        @staticmethod
        def formatar_moeda_br(valor):
            numero = float(valor or 0)
            texto = f"{numero:,.2f}"
            texto = texto.replace(",", "_").replace(".", ",").replace("_", ".")
            return f"R$ {texto}"

        @staticmethod
        def _float_seguro(valor, padrao=0.0):
            try:
                return float(valor)
            except (TypeError, ValueError):
                return padrao

        @staticmethod
        def calcular_estoque(registro, hoje=None):
            hoje = pd.to_datetime(hoje or datetime.now()).to_pydatetime()
            data_inicio = pd.to_datetime(registro.get(_CoreFallback.COL_DATA_INICIO), errors="coerce")
            qtd_total = _CoreFallback._float_seguro(registro.get(_CoreFallback.COL_QTD_TOTAL))
            dose = _CoreFallback._float_seguro(registro.get(_CoreFallback.COL_DOSE_DIARIA))

            if pd.isna(data_inicio):
                dias_passados = 0
            else:
                dias_passados = max(0, (hoje - data_inicio.to_pydatetime()).days)

            if dose <= 0:
                atual = max(0.0, qtd_total)
                resta = 0.0
            else:
                atual = max(0.0, qtd_total - (dias_passados * dose))
                resta = float(atual / dose)

            status = _CoreFallback.classificar_estoque(resta, dose)
            data_fim = hoje + timedelta(days=resta) if dose > 0 else hoje
            status_texto = status["status_texto"]
            if dose > 0 and resta > 0:
                status_texto = f"Termino: {data_fim.strftime('%d/%m/%Y')}"

            return {
                "data_inicio": data_inicio,
                "dias_passados": dias_passados,
                "qtd_total": qtd_total,
                "dose": dose,
                "atual": atual,
                "resta": resta,
                "data_fim": data_fim,
                "status_nome": status["status_nome"],
                "status_texto": status_texto,
                "status_classe": status["status_classe"],
                "card_classe": status["card_classe"],
                "prioridade": status["prioridade"],
            }

        @staticmethod
        def classificar_estoque(resta, dose):
            if dose <= 0:
                return {
                    "status_nome": "Dose invalida",
                    "status_texto": "",
                    "status_classe": "medicine-empty",
                    "card_classe": "medicine-critical",
                    "prioridade": 0,
                }
            if resta <= 0:
                return {
                    "status_nome": "Zerado",
                    "status_texto": "Estoque zerado",
                    "status_classe": "medicine-empty",
                    "card_classe": "medicine-critical",
                    "prioridade": 0,
                }
            if resta <= 3:
                return {
                    "status_nome": "Critico",
                    "status_texto": "",
                    "status_classe": "medicine-empty",
                    "card_classe": "medicine-critical",
                    "prioridade": 1,
                }
            if resta <= 7:
                return {
                    "status_nome": "Atencao",
                    "status_texto": "",
                    "status_classe": "",
                    "card_classe": "medicine-warning",
                    "prioridade": 2,
                }
            return {
                "status_nome": "Normal",
                "status_texto": "",
                "status_classe": "",
                "card_classe": "",
                "prioridade": 3,
            }

        @staticmethod
        def montar_gastos_unificados(df_com, df_con):
            registros = []

            if not df_com.empty:
                compras = df_com.copy()
                compras[_CoreFallback.COL_DATA_COMPRA] = pd.to_datetime(
                    compras[_CoreFallback.COL_DATA_COMPRA], errors="coerce"
                )
                for _, item in compras.iterrows():
                    registros.append(
                        {
                            "data": item[_CoreFallback.COL_DATA_COMPRA],
                            "mes_ano": "",
                            "tipo": _CoreFallback.TIPO_REMEDIO,
                            "descricao": item.get(_CoreFallback.COL_NOME_REMEDIO, ""),
                            "valor": _CoreFallback._float_seguro(item.get(_CoreFallback.COL_VALOR)),
                            "origem": _CoreFallback.TABELA_COMPRAS,
                            "id_origem": item.get(_CoreFallback.COL_ID, ""),
                        }
                    )

            if not df_con.empty:
                consultas = df_con.copy()
                consultas[_CoreFallback.COL_DATA_CONSULTA] = pd.to_datetime(
                    consultas[_CoreFallback.COL_DATA_CONSULTA], errors="coerce"
                )
                for _, item in consultas.iterrows():
                    registros.append(
                        {
                            "data": item[_CoreFallback.COL_DATA_CONSULTA],
                            "mes_ano": "",
                            "tipo": _CoreFallback.TIPO_CONSULTA,
                            "descricao": item.get(_CoreFallback.COL_MEDICO, ""),
                            "valor": _CoreFallback._float_seguro(item.get(_CoreFallback.COL_VALOR)),
                            "origem": _CoreFallback.TABELA_CONSULTAS,
                            "id_origem": item.get(_CoreFallback.COL_ID, ""),
                        }
                    )

            df_gastos = pd.DataFrame(registros, columns=_CoreFallback.COLUNAS_GASTOS)
            if not df_gastos.empty:
                df_gastos = df_gastos.dropna(subset=["data"]).sort_values("data", ascending=False)
                df_gastos["mes_ano"] = df_gastos["data"].dt.strftime("%Y-%m")
                df_gastos["data"] = df_gastos["data"].dt.strftime("%Y-%m-%d")

            return df_gastos

        @staticmethod
        def anos_disponiveis(df_gastos, ano_padrao=None):
            ano_padrao = ano_padrao or datetime.now().year
            if df_gastos.empty:
                return [ano_padrao]

            datas = pd.to_datetime(df_gastos["data"], errors="coerce").dropna()
            anos = sorted(datas.dt.year.unique().tolist())
            return anos or [ano_padrao]

        @staticmethod
        def filtrar_gastos(df_gastos, ano, mes=None):
            if df_gastos.empty:
                return df_gastos.copy()

            datas = pd.to_datetime(df_gastos["data"], errors="coerce")
            filtro = datas.dt.year == ano
            if isinstance(mes, int):
                filtro = filtro & (datas.dt.month == mes)
            return df_gastos[filtro].copy()

        @staticmethod
        def totais_por_tipo(df_gastos):
            if df_gastos.empty:
                return 0.0, 0.0

            total_remedios = df_gastos.loc[
                df_gastos["tipo"] == _CoreFallback.TIPO_REMEDIO, "valor"
            ].sum()
            total_consultas = df_gastos.loc[
                df_gastos["tipo"] == _CoreFallback.TIPO_CONSULTA, "valor"
            ].sum()
            return float(total_remedios), float(total_consultas)

        @staticmethod
        def resumo_mensal(df_gastos):
            if df_gastos.empty:
                return pd.DataFrame(
                    columns=["mes_ano", _CoreFallback.TIPO_REMEDIO, _CoreFallback.TIPO_CONSULTA, "Total"]
                )

            resumo = (
                df_gastos.pivot_table(
                    index="mes_ano",
                    columns="tipo",
                    values="valor",
                    aggfunc="sum",
                    fill_value=0,
                )
                .reset_index()
                .sort_values("mes_ano")
            )

            for coluna in [_CoreFallback.TIPO_REMEDIO, _CoreFallback.TIPO_CONSULTA]:
                if coluna not in resumo:
                    resumo[coluna] = 0.0
            resumo["Total"] = resumo[_CoreFallback.TIPO_REMEDIO] + resumo[_CoreFallback.TIPO_CONSULTA]
            return resumo[["mes_ano", _CoreFallback.TIPO_REMEDIO, _CoreFallback.TIPO_CONSULTA, "Total"]]

        @staticmethod
        def dataframe_com_moeda(df, coluna=COL_VALOR):
            df_visual = df.copy()
            if coluna in df_visual:
                df_visual[coluna] = df_visual[coluna].map(_CoreFallback.formatar_moeda_br)
            return df_visual

    core = _CoreFallback


# --- 1. CONFIGURACOES ---
URL_BASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
TELEGRAM_BOT_TOKEN = "8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM"
TELEGRAM_CHAT_ID = "5256921022"
APP_PASSWORD = "1234"

HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}


def enviar_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    try:
        res = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
            timeout=5,
        )
        return res.status_code == 200
    except Exception:
        return False


def requisicao_supabase(metodo, tabela, erro_contexto, **kwargs):
    if not API_KEY:
        st.error("Configure SUPABASE_API_KEY em .streamlit/secrets.toml.")
        return False

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
        st.error(f"{erro_contexto}. Codigo: {res.status_code}. Resposta: {res.text[:180]}")
        return False
    except Exception as exc:
        st.error(f"{erro_contexto}. Detalhe: {exc}")
        return False


@st.cache_data(ttl=1)
def buscar_dados(tabela):
    if not API_KEY:
        return pd.DataFrame()

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


# --- 2. CONFIGURACAO DE TELA E CSS ---
st.set_page_config(
    page_title="Saude Rock",
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

def renderizar_menu_lateral():
    with st.sidebar:
        st.title("ADM")
        if not st.session_state.autenticado:
            senha = st.text_input("Senha", type="password")
            if st.button("Entrar") or senha == APP_PASSWORD:
                if senha == APP_PASSWORD:
                    st.session_state.autenticado = True
                    st.rerun()
        else:
            st.selectbox("Tema visual", list(PALETAS.keys()), key="tema_visual")
            if st.button("Sair"):
                st.session_state.autenticado = False
                st.rerun()


def renderizar_topo():
    st.markdown("<h3 class='app-title'>Minha Saude</h3>", unsafe_allow_html=True)
    st.markdown("<p class='app-subtitle'>Controle de remedios, consultas e gastos</p>", unsafe_allow_html=True)
    return st.segmented_control(
        "Menu",
        options=["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"],
        default="Estoque",
        label_visibility="collapsed",
    )


def renderizar_alerta_estoque(remedio, estoque):
    alerta_ja_enviado = bool(remedio.get(core.COL_ALERTA_ENVIADO, False))
    remedio_id = remedio.get(core.COL_ID)

    if (
        0 < estoque["resta"] <= 7
        and not alerta_ja_enviado
        and remedio_id not in st.session_state.alertas_enviados
    ):
        telegram_ok = enviar_telegram(
            f"{remedio[core.COL_NOME]} acaba em {int(estoque['resta'])} dias!"
        )
        st.session_state.alertas_enviados.append(remedio_id)
        if telegram_ok:
            requisicao_supabase(
                "PATCH",
                f"{core.TABELA_REMEDIOS}?id=eq.{remedio_id}",
                "Alerta enviado, mas nao foi possivel marcar como enviado no banco",
                json={core.COL_ALERTA_ENVIADO: True},
            )
            st.cache_data.clear()
        else:
            st.warning(f"Nao foi possivel enviar o alerta do Telegram para {remedio[core.COL_NOME]}.")


def renderizar_card_estoque(remedio, estoque):
    st.markdown(
        f"""
        <div class="medicine-card {estoque['card_classe']}">
            <div class="medicine-name">
                <div class="medicine-title">{escape(str(remedio[core.COL_NOME]).upper())}</div>
                <div class="medicine-status">{estoque['status_nome']}</div>
                <div class="medicine-date {estoque['status_classe']}">{estoque['status_texto']}</div>
            </div>
            <div class="medicine-pill">
                <div class="medicine-label">Qtd</div>
                <div class="medicine-value">{estoque['atual']:g}</div>
            </div>
            <div class="medicine-pill">
                <div class="medicine-label">Dose</div>
                <div class="medicine-value">{estoque['dose']:g}</div>
            </div>
            <div class="medicine-pill">
                <div class="medicine-label">Dias</div>
                <div class="medicine-value">{int(estoque['resta'])}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_ajuste_estoque(remedio, estoque, hoje):
    if not st.session_state.autenticado:
        return

    remedio_id = remedio[core.COL_ID]
    with st.expander("Ajustar Estoque"):
        v_add = st.number_input("Qtd Comprada", 0.0, key=f"a_{remedio_id}")
        v_pago = st.number_input("Valor Pago R$", 0.0, key=f"p_{remedio_id}")
        data_compra = st.date_input("Data da compra", value=hoje.date(), key=f"d_{remedio_id}")
        if st.button("Salvar Registro", key=f"b_{remedio_id}", use_container_width=True):
            if v_add <= 0:
                st.error("Informe uma quantidade comprada maior que zero.")
                st.stop()
            if v_pago < 0:
                st.error("O valor pago nao pode ser negativo.")
                st.stop()

            ok_estoque = requisicao_supabase(
                "PATCH",
                f"{core.TABELA_REMEDIOS}?id=eq.{remedio_id}",
                "Nao foi possivel atualizar o estoque",
                json={
                    core.COL_QTD_TOTAL: float(estoque["atual"] + v_add),
                    core.COL_DATA_INICIO: hoje.strftime("%Y-%m-%d"),
                    core.COL_ALERTA_ENVIADO: False,
                },
            )
            if not ok_estoque:
                st.stop()

            ok_compra = requisicao_supabase(
                "POST",
                core.TABELA_COMPRAS,
                "Estoque atualizado, mas nao foi possivel registrar a compra",
                json={
                    core.COL_NOME_REMEDIO: remedio[core.COL_NOME],
                    core.COL_VALOR: float(v_pago),
                    core.COL_DATA_COMPRA: core.data_iso(data_compra),
                },
            )
            if not ok_compra:
                st.stop()

            telegram_ok = enviar_telegram(
                "Estoque atualizado\n"
                f"Remedio: {remedio[core.COL_NOME]}\n"
                f"Qtd comprada: {v_add:g}\n"
                f"Estoque atual: {estoque['atual'] + v_add:g}\n"
                f"Dias estimados: {int((estoque['atual'] + v_add) / estoque['dose']) if estoque['dose'] > 0 else 0}\n"
                f"Valor pago: {core.formatar_moeda_br(v_pago)}"
            )
            if not telegram_ok:
                st.warning("Estoque salvo, mas nao foi possivel enviar o alerta no Telegram.")
            st.cache_data.clear()
            avisar_sucesso("Estoque atualizado com sucesso.")
            st.rerun()


def tela_estoque():
    df = buscar_dados(core.TABELA_REMEDIOS)
    if df.empty:
        st.info("Nenhum remedio cadastrado ainda.")
        return

    hoje = datetime.now()
    remedios_ordenados = []
    for _, remedio in df.iterrows():
        estoque = core.calcular_estoque(remedio, hoje)
        nome_ordem = core.texto_normalizado(remedio.get(core.COL_NOME, ""))
        remedios_ordenados.append((estoque["prioridade"], nome_ordem, remedio, estoque))

    for _, _, remedio, estoque in sorted(remedios_ordenados, key=lambda item: (item[0], item[1])):
        renderizar_alerta_estoque(remedio, estoque)
        with st.container(border=True):
            renderizar_card_estoque(remedio, estoque)

            if estoque["dose"] <= 0:
                st.warning("Dose diaria precisa ser maior que zero.")
            elif estoque["resta"] <= 0:
                st.error("Estoque Zerado")

            renderizar_ajuste_estoque(remedio, estoque, hoje)


def tela_financeiro():
    st.subheader("Gastos Mensais")
    df_com = buscar_dados(core.TABELA_COMPRAS)
    df_con = buscar_dados(core.TABELA_CONSULTAS)
    df_gastos = core.montar_gastos_unificados(df_com, df_con)

    ano_atual = datetime.now().year
    anos = core.anos_disponiveis(df_gastos, ano_atual)
    indice_ano = anos.index(ano_atual) if ano_atual in anos else len(anos) - 1
    opcoes_mes = ["Todos"] + [f"{numero:02d} - {nome}" for numero, nome in core.MESES.items()]

    col_a, col_m = st.columns(2)
    ano_sel = col_a.selectbox("Ano", anos, index=indice_ano)
    mes_rotulo = col_m.selectbox("Mes", opcoes_mes, index=0)
    mes_sel = None if mes_rotulo == "Todos" else int(mes_rotulo.split(" - ")[0])

    filtro_mes = core.filtrar_gastos(df_gastos, ano_sel, mes_sel)
    df_ano = core.filtrar_gastos(df_gastos, ano_sel)
    total_r, total_c = core.totais_por_tipo(filtro_mes)

    resumo = core.resumo_mensal(df_ano)
    if not resumo.empty:
        st.write("**Resumo por mes:**")
        st.bar_chart(resumo.set_index("mes_ano")[[core.TIPO_REMEDIO, core.TIPO_CONSULTA]])

        resumo_visual = resumo.copy()
        for coluna in [core.TIPO_REMEDIO, core.TIPO_CONSULTA, "Total"]:
            resumo_visual[coluna] = resumo_visual[coluna].map(core.formatar_moeda_br)
        st.dataframe(resumo_visual, hide_index=True, use_container_width=True)

    if not filtro_mes.empty:
        st.write("**Detalhamento unificado:**")
        df_visual = core.dataframe_com_moeda(filtro_mes[core.COLUNAS_GASTOS_VISIVEIS])
        st.dataframe(df_visual, hide_index=True, use_container_width=True)
    else:
        st.info("Nenhum gasto encontrado para esse filtro.")

    st.divider()
    st.metric("TOTAL INVESTIDO", core.formatar_moeda_br(total_r + total_c))
    st.info(
        f"Remedios: {core.formatar_moeda_br(total_r)} | "
        f"Consultas: {core.formatar_moeda_br(total_c)}"
    )
    if not df_gastos.empty:
        st.download_button(
            "Baixar planilha unificada",
            data=dataframe_para_csv(df_gastos),
            file_name="gastos_unificados_power_bi.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("Ainda nao ha dados financeiros para baixar.")


def tela_consultas():
    df = buscar_dados(core.TABELA_CONSULTAS)
    if df.empty:
        st.info("Nenhuma consulta cadastrada ainda.")
        return

    df_consultas = df[core.COLUNAS_CONSULTA_VISIVEIS].copy()
    st.dataframe(core.dataframe_com_moeda(df_consultas), hide_index=True, use_container_width=True)
    st.download_button(
        "Baixar planilha de consultas",
        data=dataframe_para_csv(df_consultas),
        file_name="consultas.csv",
        mime="text/csv",
        use_container_width=True,
    )


def cadastrar_remedio():
    n = st.text_input("Nome")
    q = st.number_input("Qtd")
    d = st.number_input("Dose/Dia")
    p = st.number_input("Preco")
    data_compra = st.date_input("Data da compra", value=datetime.now().date())

    if not st.form_submit_button("Salvar", use_container_width=True):
        return

    nome_limpo = n.strip()
    if not nome_limpo:
        st.error("Informe o nome do remedio.")
        st.stop()
    if q <= 0:
        st.error("Informe uma quantidade maior que zero.")
        st.stop()
    if d <= 0:
        st.error("Informe uma dose por dia maior que zero.")
        st.stop()
    if p < 0:
        st.error("O preco nao pode ser negativo.")
        st.stop()

    df_remedios = buscar_dados(core.TABELA_REMEDIOS)
    if not df_remedios.empty and core.COL_NOME in df_remedios:
        nomes_existentes = df_remedios[core.COL_NOME].map(core.texto_normalizado)
        if core.texto_normalizado(nome_limpo) in set(nomes_existentes):
            st.error("Ja existe um remedio cadastrado com esse nome.")
            st.stop()

    ok_remedio = requisicao_supabase(
        "POST",
        core.TABELA_REMEDIOS,
        "Nao foi possivel cadastrar o remedio",
        json={
            core.COL_NOME: nome_limpo,
            core.COL_QTD_TOTAL: float(q),
            core.COL_DOSE_DIARIA: float(d),
            core.COL_DATA_INICIO: datetime.now().strftime("%Y-%m-%d"),
            core.COL_ALERTA_ENVIADO: False,
        },
    )
    if not ok_remedio:
        st.stop()

    ok_compra = requisicao_supabase(
        "POST",
        core.TABELA_COMPRAS,
        "Remedio cadastrado, mas nao foi possivel registrar a compra",
        json={
            core.COL_NOME_REMEDIO: nome_limpo,
            core.COL_VALOR: float(p),
            core.COL_DATA_COMPRA: core.data_iso(data_compra),
        },
    )
    if not ok_compra:
        st.stop()
    st.cache_data.clear()
    avisar_sucesso("Remedio cadastrado com sucesso.")
    st.rerun()


def cadastrar_consulta():
    m = st.text_input("Medico")
    v = st.number_input("Valor")
    data_consulta = st.date_input("Data da consulta", value=datetime.now().date())

    if not st.form_submit_button("Salvar", use_container_width=True):
        return

    medico_limpo = m.strip()
    data_consulta_str = core.data_iso(data_consulta)
    if not medico_limpo:
        st.error("Informe o medico ou descricao da consulta.")
        st.stop()
    if v <= 0:
        st.error("Informe um valor maior que zero.")
        st.stop()

    df_consultas = buscar_dados(core.TABELA_CONSULTAS)
    if not df_consultas.empty:
        consultas = df_consultas.copy()
        consultas[core.COL_DATA_CONSULTA] = pd.to_datetime(
            consultas[core.COL_DATA_CONSULTA], errors="coerce"
        ).dt.strftime("%Y-%m-%d")
        consultas[core.COL_VALOR] = pd.to_numeric(consultas[core.COL_VALOR], errors="coerce")
        duplicada = consultas[
            (consultas[core.COL_MEDICO].map(core.texto_normalizado) == core.texto_normalizado(medico_limpo))
            & (consultas[core.COL_DATA_CONSULTA] == data_consulta_str)
            & (consultas[core.COL_VALOR] == float(v))
        ]
        if not duplicada.empty:
            st.error("Essa consulta ja foi cadastrada nessa data com o mesmo valor.")
            st.stop()

    ok_consulta = requisicao_supabase(
        "POST",
        core.TABELA_CONSULTAS,
        "Nao foi possivel cadastrar a consulta",
        json={
            core.COL_MEDICO: medico_limpo,
            core.COL_VALOR: float(v),
            core.COL_DATA_CONSULTA: data_consulta_str,
        },
    )
    if not ok_consulta:
        st.stop()
    st.cache_data.clear()
    avisar_sucesso("Consulta cadastrada com sucesso.")
    st.rerun()


def tela_cadastrar():
    if not st.session_state.autenticado:
        st.warning("Acesse o menu ADM na lateral.")
        return

    tipo = st.segmented_control("Tipo", [core.TIPO_REMEDIO, core.TIPO_CONSULTA], default=core.TIPO_REMEDIO)
    with st.form("cad"):
        if tipo == core.TIPO_REMEDIO:
            cadastrar_remedio()
        else:
            cadastrar_consulta()


def tela_remover():
    if not st.session_state.autenticado:
        st.warning("Acesse o menu ADM na lateral.")
        return

    tab = st.selectbox("Tabela", [core.TABELA_REMEDIOS, core.TABELA_CONSULTAS, core.TABELA_COMPRAS])
    df_del = buscar_dados(tab)
    if df_del.empty:
        st.info("Nao ha itens para remover nessa tabela.")
        return

    coluna_nome = (
        core.COL_NOME
        if tab == core.TABELA_REMEDIOS
        else (core.COL_NOME_REMEDIO if tab == core.TABELA_COMPRAS else core.COL_MEDICO)
    )
    item = st.selectbox("Item", df_del[coluna_nome].tolist())
    if st.button("Apagar registro", type="primary", use_container_width=True):
        id_i = df_del[df_del[coluna_nome] == item][core.COL_ID].values[0]
        ok_delete = requisicao_supabase(
            "DELETE",
            f"{tab}?id=eq.{id_i}",
            "Nao foi possivel remover o item",
        )
        if not ok_delete:
            st.stop()
        if tab == core.TABELA_REMEDIOS:
            ok_compras = requisicao_supabase(
                "DELETE",
                f"{core.TABELA_COMPRAS}?{core.COL_NOME_REMEDIO}=eq.{item}",
                "Remedio removido, mas nao foi possivel remover as compras relacionadas",
            )
            if not ok_compras:
                st.stop()
        st.cache_data.clear()
        avisar_sucesso("Item removido com sucesso.")
        st.rerun()


def main():
    if not API_KEY:
        st.warning("Configure SUPABASE_API_KEY em .streamlit/secrets.toml para conectar ao Supabase.")

    renderizar_menu_lateral()
    aba = renderizar_topo()
    mostrar_mensagem_sucesso()

    if aba == "Estoque":
        tela_estoque()
    elif aba == "Financeiro":
        tela_financeiro()
    elif aba == "Consultas":
        tela_consultas()
    elif aba == "Cadastrar":
        tela_cadastrar()
    elif aba == "Remover":
        tela_remover()


main()


import saude_core as core


# --- 1. CONFIGURACOES ---
URL_BASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
TELEGRAM_BOT_TOKEN = "8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM"
TELEGRAM_CHAT_ID = "5256921022"
APP_PASSWORD = "1234"

HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}


def enviar_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    try:
        res = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
            timeout=5,
        )
        return res.status_code == 200
    except Exception:
        return False


def requisicao_supabase(metodo, tabela, erro_contexto, **kwargs):
    if not API_KEY:
        st.error("Configure SUPABASE_API_KEY em .streamlit/secrets.toml.")
        return False

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
        st.error(f"{erro_contexto}. Codigo: {res.status_code}. Resposta: {res.text[:180]}")
        return False
    except Exception as exc:
        st.error(f"{erro_contexto}. Detalhe: {exc}")
        return False


@st.cache_data(ttl=1)
def buscar_dados(tabela):
    if not API_KEY:
        return pd.DataFrame()

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


# --- 2. CONFIGURACAO DE TELA E CSS ---
st.set_page_config(
    page_title="Saude Rock",
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

def renderizar_menu_lateral():
    with st.sidebar:
        st.title("ADM")
        if not st.session_state.autenticado:
            senha = st.text_input("Senha", type="password")
            if st.button("Entrar") or senha == APP_PASSWORD:
                if senha == APP_PASSWORD:
                    st.session_state.autenticado = True
                    st.rerun()
        else:
            st.selectbox("Tema visual", list(PALETAS.keys()), key="tema_visual")
            if st.button("Sair"):
                st.session_state.autenticado = False
                st.rerun()


def renderizar_topo():
    st.markdown("<h3 class='app-title'>Minha Saude</h3>", unsafe_allow_html=True)
    st.markdown("<p class='app-subtitle'>Controle de remedios, consultas e gastos</p>", unsafe_allow_html=True)
    return st.segmented_control(
        "Menu",
        options=["Estoque", "Financeiro", "Consultas", "Cadastrar", "Remover"],
        default="Estoque",
        label_visibility="collapsed",
    )


def renderizar_alerta_estoque(remedio, estoque):
    alerta_ja_enviado = bool(remedio.get(core.COL_ALERTA_ENVIADO, False))
    remedio_id = remedio.get(core.COL_ID)

    if (
        0 < estoque["resta"] <= 7
        and not alerta_ja_enviado
        and remedio_id not in st.session_state.alertas_enviados
    ):
        telegram_ok = enviar_telegram(
            f"{remedio[core.COL_NOME]} acaba em {int(estoque['resta'])} dias!"
        )
        st.session_state.alertas_enviados.append(remedio_id)
        if telegram_ok:
            requisicao_supabase(
                "PATCH",
                f"{core.TABELA_REMEDIOS}?id=eq.{remedio_id}",
                "Alerta enviado, mas nao foi possivel marcar como enviado no banco",
                json={core.COL_ALERTA_ENVIADO: True},
            )
            st.cache_data.clear()
        else:
            st.warning(f"Nao foi possivel enviar o alerta do Telegram para {remedio[core.COL_NOME]}.")


def renderizar_card_estoque(remedio, estoque):
    st.markdown(
        f"""
        <div class="medicine-card {estoque['card_classe']}">
            <div class="medicine-name">
                <div class="medicine-title">{escape(str(remedio[core.COL_NOME]).upper())}</div>
                <div class="medicine-status">{estoque['status_nome']}</div>
                <div class="medicine-date {estoque['status_classe']}">{estoque['status_texto']}</div>
            </div>
            <div class="medicine-pill">
                <div class="medicine-label">Qtd</div>
                <div class="medicine-value">{estoque['atual']:g}</div>
            </div>
            <div class="medicine-pill">
                <div class="medicine-label">Dose</div>
                <div class="medicine-value">{estoque['dose']:g}</div>
            </div>
            <div class="medicine-pill">
                <div class="medicine-label">Dias</div>
                <div class="medicine-value">{int(estoque['resta'])}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_ajuste_estoque(remedio, estoque, hoje):
    if not st.session_state.autenticado:
        return

    remedio_id = remedio[core.COL_ID]
    with st.expander("Ajustar Estoque"):
        v_add = st.number_input("Qtd Comprada", 0.0, key=f"a_{remedio_id}")
        v_pago = st.number_input("Valor Pago R$", 0.0, key=f"p_{remedio_id}")
        data_compra = st.date_input("Data da compra", value=hoje.date(), key=f"d_{remedio_id}")
        if st.button("Salvar Registro", key=f"b_{remedio_id}", use_container_width=True):
            if v_add <= 0:
                st.error("Informe uma quantidade comprada maior que zero.")
                st.stop()
            if v_pago < 0:
                st.error("O valor pago nao pode ser negativo.")
                st.stop()

            ok_estoque = requisicao_supabase(
                "PATCH",
                f"{core.TABELA_REMEDIOS}?id=eq.{remedio_id}",
                "Nao foi possivel atualizar o estoque",
                json={
                    core.COL_QTD_TOTAL: float(estoque["atual"] + v_add),
                    core.COL_DATA_INICIO: hoje.strftime("%Y-%m-%d"),
                    core.COL_ALERTA_ENVIADO: False,
                },
            )
            if not ok_estoque:
                st.stop()

            ok_compra = requisicao_supabase(
                "POST",
                core.TABELA_COMPRAS,
                "Estoque atualizado, mas nao foi possivel registrar a compra",
                json={
                    core.COL_NOME_REMEDIO: remedio[core.COL_NOME],
                    core.COL_VALOR: float(v_pago),
                    core.COL_DATA_COMPRA: core.data_iso(data_compra),
                },
            )
            if not ok_compra:
                st.stop()

            telegram_ok = enviar_telegram(
                "Estoque atualizado\n"
                f"Remedio: {remedio[core.COL_NOME]}\n"
                f"Qtd comprada: {v_add:g}\n"
                f"Estoque atual: {estoque['atual'] + v_add:g}\n"
                f"Dias estimados: {int((estoque['atual'] + v_add) / estoque['dose']) if estoque['dose'] > 0 else 0}\n"
                f"Valor pago: {core.formatar_moeda_br(v_pago)}"
            )
            if not telegram_ok:
                st.warning("Estoque salvo, mas nao foi possivel enviar o alerta no Telegram.")
            st.cache_data.clear()
            avisar_sucesso("Estoque atualizado com sucesso.")
            st.rerun()


def tela_estoque():
    df = buscar_dados(core.TABELA_REMEDIOS)
    if df.empty:
        st.info("Nenhum remedio cadastrado ainda.")
        return

    hoje = datetime.now()
    remedios_ordenados = []
    for _, remedio in df.iterrows():
        estoque = core.calcular_estoque(remedio, hoje)
        nome_ordem = core.texto_normalizado(remedio.get(core.COL_NOME, ""))
        remedios_ordenados.append((estoque["prioridade"], nome_ordem, remedio, estoque))

    for _, _, remedio, estoque in sorted(remedios_ordenados, key=lambda item: (item[0], item[1])):
        renderizar_alerta_estoque(remedio, estoque)
        with st.container(border=True):
            renderizar_card_estoque(remedio, estoque)

            if estoque["dose"] <= 0:
                st.warning("Dose diaria precisa ser maior que zero.")
            elif estoque["resta"] <= 0:
                st.error("Estoque Zerado")

            renderizar_ajuste_estoque(remedio, estoque, hoje)


def tela_financeiro():
    st.subheader("Gastos Mensais")
    df_com = buscar_dados(core.TABELA_COMPRAS)
    df_con = buscar_dados(core.TABELA_CONSULTAS)
    df_gastos = core.montar_gastos_unificados(df_com, df_con)

    ano_atual = datetime.now().year
    anos = core.anos_disponiveis(df_gastos, ano_atual)
    indice_ano = anos.index(ano_atual) if ano_atual in anos else len(anos) - 1
    opcoes_mes = ["Todos"] + [f"{numero:02d} - {nome}" for numero, nome in core.MESES.items()]

    col_a, col_m = st.columns(2)
    ano_sel = col_a.selectbox("Ano", anos, index=indice_ano)
    mes_rotulo = col_m.selectbox("Mes", opcoes_mes, index=0)
    mes_sel = None if mes_rotulo == "Todos" else int(mes_rotulo.split(" - ")[0])

    filtro_mes = core.filtrar_gastos(df_gastos, ano_sel, mes_sel)
    df_ano = core.filtrar_gastos(df_gastos, ano_sel)
    total_r, total_c = core.totais_por_tipo(filtro_mes)

    resumo = core.resumo_mensal(df_ano)
    if not resumo.empty:
        st.write("**Resumo por mes:**")
        st.bar_chart(resumo.set_index("mes_ano")[[core.TIPO_REMEDIO, core.TIPO_CONSULTA]])

        resumo_visual = resumo.copy()
        for coluna in [core.TIPO_REMEDIO, core.TIPO_CONSULTA, "Total"]:
            resumo_visual[coluna] = resumo_visual[coluna].map(core.formatar_moeda_br)
        st.dataframe(resumo_visual, hide_index=True, use_container_width=True)

    if not filtro_mes.empty:
        st.write("**Detalhamento unificado:**")
        df_visual = core.dataframe_com_moeda(filtro_mes[core.COLUNAS_GASTOS_VISIVEIS])
        st.dataframe(df_visual, hide_index=True, use_container_width=True)
    else:
        st.info("Nenhum gasto encontrado para esse filtro.")

    st.divider()
    st.metric("TOTAL INVESTIDO", core.formatar_moeda_br(total_r + total_c))
    st.info(
        f"Remedios: {core.formatar_moeda_br(total_r)} | "
        f"Consultas: {core.formatar_moeda_br(total_c)}"
    )
    if not df_gastos.empty:
        st.download_button(
            "Baixar planilha unificada",
            data=dataframe_para_csv(df_gastos),
            file_name="gastos_unificados_power_bi.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("Ainda nao ha dados financeiros para baixar.")


def tela_consultas():
    df = buscar_dados(core.TABELA_CONSULTAS)
    if df.empty:
        st.info("Nenhuma consulta cadastrada ainda.")
        return

    df_consultas = df[core.COLUNAS_CONSULTA_VISIVEIS].copy()
    st.dataframe(core.dataframe_com_moeda(df_consultas), hide_index=True, use_container_width=True)
    st.download_button(
        "Baixar planilha de consultas",
        data=dataframe_para_csv(df_consultas),
        file_name="consultas.csv",
        mime="text/csv",
        use_container_width=True,
    )


def cadastrar_remedio():
    n = st.text_input("Nome")
    q = st.number_input("Qtd")
    d = st.number_input("Dose/Dia")
    p = st.number_input("Preco")
    data_compra = st.date_input("Data da compra", value=datetime.now().date())

    if not st.form_submit_button("Salvar", use_container_width=True):
        return

    nome_limpo = n.strip()
    if not nome_limpo:
        st.error("Informe o nome do remedio.")
        st.stop()
    if q <= 0:
        st.error("Informe uma quantidade maior que zero.")
        st.stop()
    if d <= 0:
        st.error("Informe uma dose por dia maior que zero.")
        st.stop()
    if p < 0:
        st.error("O preco nao pode ser negativo.")
        st.stop()

    df_remedios = buscar_dados(core.TABELA_REMEDIOS)
    if not df_remedios.empty and core.COL_NOME in df_remedios:
        nomes_existentes = df_remedios[core.COL_NOME].map(core.texto_normalizado)
        if core.texto_normalizado(nome_limpo) in set(nomes_existentes):
            st.error("Ja existe um remedio cadastrado com esse nome.")
            st.stop()

    ok_remedio = requisicao_supabase(
        "POST",
        core.TABELA_REMEDIOS,
        "Nao foi possivel cadastrar o remedio",
        json={
            core.COL_NOME: nome_limpo,
            core.COL_QTD_TOTAL: float(q),
            core.COL_DOSE_DIARIA: float(d),
            core.COL_DATA_INICIO: datetime.now().strftime("%Y-%m-%d"),
            core.COL_ALERTA_ENVIADO: False,
        },
    )
    if not ok_remedio:
        st.stop()

    ok_compra = requisicao_supabase(
        "POST",
        core.TABELA_COMPRAS,
        "Remedio cadastrado, mas nao foi possivel registrar a compra",
        json={
            core.COL_NOME_REMEDIO: nome_limpo,
            core.COL_VALOR: float(p),
            core.COL_DATA_COMPRA: core.data_iso(data_compra),
        },
    )
    if not ok_compra:
        st.stop()
    st.cache_data.clear()
    avisar_sucesso("Remedio cadastrado com sucesso.")
    st.rerun()


def cadastrar_consulta():
    m = st.text_input("Medico")
    v = st.number_input("Valor")
    data_consulta = st.date_input("Data da consulta", value=datetime.now().date())

    if not st.form_submit_button("Salvar", use_container_width=True):
        return

    medico_limpo = m.strip()
    data_consulta_str = core.data_iso(data_consulta)
    if not medico_limpo:
        st.error("Informe o medico ou descricao da consulta.")
        st.stop()
    if v <= 0:
        st.error("Informe um valor maior que zero.")
        st.stop()

    df_consultas = buscar_dados(core.TABELA_CONSULTAS)
    if not df_consultas.empty:
        consultas = df_consultas.copy()
        consultas[core.COL_DATA_CONSULTA] = pd.to_datetime(
            consultas[core.COL_DATA_CONSULTA], errors="coerce"
        ).dt.strftime("%Y-%m-%d")
        consultas[core.COL_VALOR] = pd.to_numeric(consultas[core.COL_VALOR], errors="coerce")
        duplicada = consultas[
            (consultas[core.COL_MEDICO].map(core.texto_normalizado) == core.texto_normalizado(medico_limpo))
            & (consultas[core.COL_DATA_CONSULTA] == data_consulta_str)
            & (consultas[core.COL_VALOR] == float(v))
        ]
        if not duplicada.empty:
            st.error("Essa consulta ja foi cadastrada nessa data com o mesmo valor.")
            st.stop()

    ok_consulta = requisicao_supabase(
        "POST",
        core.TABELA_CONSULTAS,
        "Nao foi possivel cadastrar a consulta",
        json={
            core.COL_MEDICO: medico_limpo,
            core.COL_VALOR: float(v),
            core.COL_DATA_CONSULTA: data_consulta_str,
        },
    )
    if not ok_consulta:
        st.stop()
    st.cache_data.clear()
    avisar_sucesso("Consulta cadastrada com sucesso.")
    st.rerun()


def tela_cadastrar():
    if not st.session_state.autenticado:
        st.warning("Acesse o menu ADM na lateral.")
        return

    tipo = st.segmented_control("Tipo", [core.TIPO_REMEDIO, core.TIPO_CONSULTA], default=core.TIPO_REMEDIO)
    with st.form("cad"):
        if tipo == core.TIPO_REMEDIO:
            cadastrar_remedio()
        else:
            cadastrar_consulta()


def tela_remover():
    if not st.session_state.autenticado:
        st.warning("Acesse o menu ADM na lateral.")
        return

    tab = st.selectbox("Tabela", [core.TABELA_REMEDIOS, core.TABELA_CONSULTAS, core.TABELA_COMPRAS])
    df_del = buscar_dados(tab)
    if df_del.empty:
        st.info("Nao ha itens para remover nessa tabela.")
        return

    coluna_nome = (
        core.COL_NOME
        if tab == core.TABELA_REMEDIOS
        else (core.COL_NOME_REMEDIO if tab == core.TABELA_COMPRAS else core.COL_MEDICO)
    )
    item = st.selectbox("Item", df_del[coluna_nome].tolist())
    if st.button("Apagar registro", type="primary", use_container_width=True):
        id_i = df_del[df_del[coluna_nome] == item][core.COL_ID].values[0]
        ok_delete = requisicao_supabase(
            "DELETE",
            f"{tab}?id=eq.{id_i}",
            "Nao foi possivel remover o item",
        )
        if not ok_delete:
            st.stop()
        if tab == core.TABELA_REMEDIOS:
            ok_compras = requisicao_supabase(
                "DELETE",
                f"{core.TABELA_COMPRAS}?{core.COL_NOME_REMEDIO}=eq.{item}",
                "Remedio removido, mas nao foi possivel remover as compras relacionadas",
            )
            if not ok_compras:
                st.stop()
        st.cache_data.clear()
        avisar_sucesso("Item removido com sucesso.")
        st.rerun()


def main():
    if not API_KEY:
        st.warning("Configure SUPABASE_API_KEY em .streamlit/secrets.toml para conectar ao Supabase.")

    renderizar_menu_lateral()
    aba = renderizar_topo()
    mostrar_mensagem_sucesso()

    if aba == "Estoque":
        tela_estoque()
    elif aba == "Financeiro":
        tela_financeiro()
    elif aba == "Consultas":
        tela_consultas()
    elif aba == "Cadastrar":
        tela_cadastrar()
    elif aba == "Remover":
        tela_remover()


main()
