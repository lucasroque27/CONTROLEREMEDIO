import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from typing import Any


st.set_page_config(page_title="Saude Familia", page_icon="💊", layout="centered")


URL_SUPABASE = "https://phvjjwrerrcnsfmrijyg.supabase.co/rest/v1/"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBodmpqd3JlcnJjbnNmbXJpanlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njc5MjMxMiwiZXhwIjoyMDkyMzY4MzEyfQ.KzhZ0xZiJ4EPqKu-Ql4NT64mV9LzoOFbn7oapBU3gTk"
TOKEN_TELEGRAM = "8256417654:AAFcjDaGFVYFCctzpIJnVoshjQx6M1A1vOM"
CHAT_ID = "5256921022"
ADMIN_PASSWORD = "1234"

HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

DATE_COLUMNS = {"data_inicio", "data_consulta", "data_compra"}


def app_ready() -> bool:
    missing = [
        name
        for name, value in {
            "URL_SUPABASE": URL_SUPABASE,
            "API_KEY": API_KEY,
        }.items()
        if not value
    ]

    if missing:
        st.error(f"Configuracao incompleta: {', '.join(missing)}.")
        st.stop()
    return True


def init_state() -> None:
    st.session_state.setdefault("admin", False)
    st.session_state.setdefault("alertas_enviados", {})


def enviar_telegram(mensagem: str) -> None:
    if not TOKEN_TELEGRAM or not CHAT_ID:
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": mensagem},
            timeout=5,
        )
    except requests.RequestException:
        pass


def parse_dataframe_dates(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    for col in DATE_COLUMNS.intersection(df.columns):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


@st.cache_data(ttl=60)
def api_get(tabela: str) -> pd.DataFrame:
    try:
        res = requests.get(
            f"{URL_SUPABASE}{tabela}?select=*&order=id.desc",
            headers=HEADERS,
            timeout=10,
        )
        res.raise_for_status()
        return parse_dataframe_dates(pd.DataFrame(res.json()))
    except requests.RequestException:
        st.warning(f"Nao foi possivel carregar a tabela '{tabela}'.")
        return pd.DataFrame()


def api_write(method: str, endpoint: str, payload: dict[str, Any] | None = None) -> bool:
    try:
        response = requests.request(
            method=method,
            url=f"{URL_SUPABASE}{endpoint}",
            headers=HEADERS,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        api_get.clear()
        return True
    except requests.RequestException:
        st.error("Nao foi possivel salvar os dados no Supabase.")
        return False


def calcular_estoque(remedio: pd.Series, hoje: datetime) -> tuple[int, int, datetime]:
    data_inicio = remedio.get("data_inicio")
    dose_diaria = float(remedio.get("dose_diaria", 0) or 0)
    qtd_total = int(remedio.get("qtd_total", 0) or 0)

    if pd.isna(data_inicio):
        data_inicio = hoje

    dias_passados = max(0, (hoje.date() - data_inicio.date()).days)
    estoque_atual = max(0, int(qtd_total - (dias_passados * dose_diaria)))
    dias_restantes = int(estoque_atual / dose_diaria) if dose_diaria > 0 else 0
    data_fim = hoje + timedelta(days=dias_restantes)
    return estoque_atual, dias_restantes, data_fim


def disparar_alerta_estoque(remedio: pd.Series, estoque_atual: int, dias_restantes: int, data_fim: datetime) -> None:
    if dias_restantes >= 7:
        return

    alerta_id = f"{remedio['id']}-{data_fim.date().isoformat()}"
    if alerta_id in st.session_state.alertas_enviados:
        return

    msg = (
        f"ALERTA: {remedio['nome']} acabando!\n\n"
        f"Estoque: {estoque_atual} un.\n"
        f"Dura mais {dias_restantes} dias.\n"
        f"Acaba em: {data_fim.strftime('%d/%m/%Y')}"
    )
    enviar_telegram(msg)
    st.session_state.alertas_enviados[alerta_id] = True


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("<h2 style='text-align: center;'>Gestao Saude</h2>", unsafe_allow_html=True)
        st.markdown("---")

        if not st.session_state.admin:
            password = st.text_input("Senha ADM", type="password")
            if st.button("Liberar", use_container_width=True):
                if password == ADMIN_PASSWORD:
                    st.session_state.admin = True
                    st.rerun()
                else:
                    st.error("Senha invalida.")
        else:
            st.success("Modo edicao ativo")
            if st.button("Sair ADM", use_container_width=True):
                st.session_state.admin = False
                st.rerun()

        st.markdown("---")
        return st.radio(
            "Navegacao",
            ["Estoque", "Historico Medico", "Financeiro", "Cadastro", "Remover"],
        )


def render_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #F7FAFF 0%, #EEF4FF 100%) !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #EAF4FF 0%, #DCEEFF 100%) !important;
            border-right: 1px solid #BFD8F5;
        }

        [data-testid="stSidebar"] hr {
            border-color: #B9D2EC !important;
        }

        header[data-testid="stHeader"] {
            background-color: rgba(255, 255, 255, 0.92) !important;
        }

        .med-card {
            background-color: #FFFFFF !important;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 12px solid #5B9DFF;
            box-shadow: 0 8px 24px rgba(44, 101, 163, 0.10);
        }

        .med-card.receita-alerta {
            background: linear-gradient(180deg, #FFF4E8 0%, #FFE9D5 100%) !important;
            border-left: 12px solid #FF8A3D !important;
            box-shadow: 0 10px 24px rgba(255, 138, 61, 0.18);
        }

        .stApp h1, .stApp h2, .stApp h3 {
            color: #14324C !important;
            font-weight: 600;
        }

        .stApp .med-card,
        .stApp .med-card p,
        .stApp .med-card span {
            color: #14324C !important;
        }

        div.stButton > button {
            width: 100%;
            border-radius: 12px;
            border: 1px solid #4F93F7 !important;
            background: linear-gradient(180deg, #69ABFF 0%, #4B91F1 100%) !important;
            color: #FFFFFF !important;
            font-weight: bold;
            box-shadow: 0 6px 16px rgba(75, 145, 241, 0.22);
        }

        div.stButton > button:hover {
            background: linear-gradient(180deg, #7AB5FF 0%, #5A9CF7 100%) !important;
            border-color: #3C84EC !important;
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="base-input"] > div,
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stDateInput > div > div input,
        .stSelectbox > div > div,
        .stTextArea textarea {
            background-color: #FFFFFF !important;
            color: #12324A !important;
            border: 1px solid #B7D1ED !important;
            border-radius: 12px !important;
        }

        .stRadio label,
        .stSelectbox label,
        .stTextInput label,
        .stNumberInput label,
        .stDateInput label {
            color: #14324C !important;
            font-weight: 700 !important;
        }

        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div {
            color: #14324C !important;
        }

        [data-testid="stSidebar"] [data-baseweb="input"] > div,
        [data-testid="stSidebar"] [data-baseweb="base-input"] > div {
            background-color: #FFFFFF !important;
            border: 1px solid #BCD5F0 !important;
        }

        [data-testid="stSidebar"] .stSuccess {
            background-color: #E6F6EC !important;
            color: #1C6B41 !important;
            border: 1px solid #B8E2C8 !important;
        }

        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def tela_estoque() -> None:
    st.title("Controle de Remedios")
    df = api_get("remedios")

    if df.empty:
        st.info("Nenhum remedio cadastrado.")
        return

    col1, col2 = st.columns([1.2, 1.1])
    with col1:
        filtro_receita = st.selectbox(
            "Filtrar por receita",
            ["Todos", "So com receita", "So sem receita"],
        )
    with col2:
        apenas_alertas = st.checkbox("Mostrar so os que estao acabando")

    hoje = datetime.now()
    exibidos = 0

    for _, remedio in df.iterrows():
        estoque_atual, dias_restantes, data_fim = calcular_estoque(remedio, hoje)
        disparar_alerta_estoque(remedio, estoque_atual, dias_restantes, data_fim)

        precisa_receita = bool(remedio.get("precisa_receita", False))
        receita = "Sim" if precisa_receita else "Nao"

        if filtro_receita == "So com receita" and not precisa_receita:
            continue
        if filtro_receita == "So sem receita" and precisa_receita:
            continue
        if apenas_alertas and dias_restantes >= 7:
            continue

        exibidos += 1
        cor = "#CC0000" if dias_restantes < 7 else "#006600"
        card_class = "med-card receita-alerta" if precisa_receita and dias_restantes < 7 else "med-card"
        aviso_receita = ""
        if precisa_receita and dias_restantes < 7:
            aviso_receita = "<p><b>Atencao:</b> esse remedio precisa de receita e esta perto de acabar.</p>"

        st.markdown(
            f"""
            <div class="{card_class}">
                <span style="font-size: 1.4em;"><b>{str(remedio['nome']).upper()}</b></span><br>
                <p>Estoque: <b>{estoque_atual} un.</b> | Dose: <b>{remedio['dose_diaria']} p/ dia</b></p>
                <p>Precisa de receita: <b>{receita}</b></p>
                {aviso_receita}
                <p style="font-size: 1.2em; color: {cor} !important;">
                    Acaba em: <b>{data_fim.strftime('%d/%m/%Y')}</b> ({dias_restantes} dias)
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not st.session_state.admin:
            continue

        with st.expander(f"Repor {remedio['nome']}"):
            with st.form(f"reposicao_{remedio['id']}"):
                nova_qtd = st.number_input("Qtd comprada agora", min_value=1, value=30, step=1)
                novo_valor = st.number_input(
                    "Preco da nova caixa",
                    min_value=0.0,
                    value=float(remedio.get("preco", 0.0) or 0.0),
                    step=0.01,
                )
                nova_receita = st.checkbox(
                    "Precisa de receita",
                    value=bool(remedio.get("precisa_receita", False)),
                    key=f"receita_{remedio['id']}",
                )
                if st.form_submit_button("Confirmar Reposicao"):
                    total_novo = estoque_atual + int(nova_qtd)
                    ok_remedio = api_write(
                        "PATCH",
                        f"remedios?id=eq.{remedio['id']}",
                        {
                            "qtd_total": total_novo,
                            "data_inicio": str(hoje.date()),
                            "preco": float(novo_valor),
                            "precisa_receita": bool(nova_receita),
                        },
                    )
                    ok_compra = api_write(
                        "POST",
                        "compras",
                        {
                            "nome_remedio": remedio["nome"],
                            "valor": float(novo_valor),
                            "data_compra": str(hoje.date()),
                        },
                    )
                    if ok_remedio and ok_compra:
                        enviar_telegram(
                            f"REPOSICAO: {remedio['nome']}\n"
                            f"Novo total: {total_novo} un.\n"
                            f"Valor: R$ {novo_valor:.2f}"
                        )
                        st.success("Reposicao registrada com sucesso.")
                        time.sleep(1)
                        st.rerun()

    if exibidos == 0:
        st.info("Nenhum remedio encontrado com esse filtro.")


def tela_historico() -> None:
    st.title("Consultas Realizadas")
    df_consultas = api_get("consultas")

    if df_consultas.empty:
        st.info("Nenhuma consulta cadastrada.")
        return

    for _, consulta in df_consultas.iterrows():
        data = consulta.get("data_consulta")
        data_fmt = data.strftime("%d/%m/%Y") if pd.notna(data) else "Sem data"
        valor = float(consulta.get("valor", 0) or 0)
        medico = consulta.get("medico", "Nao informado")
        st.markdown(
            f"""
            <div class="med-card">
                <b>{data_fmt}</b><br>
                Dr. {medico}<br>
                R$ {valor:.2f}
            </div>
            """,
            unsafe_allow_html=True,
        )


def tela_financeiro() -> None:
    st.title("Resumo Financeiro")
    df_compras = api_get("compras")
    df_consultas = api_get("consultas")

    total_compras = df_compras["valor"].sum() if not df_compras.empty and "valor" in df_compras else 0
    total_consultas = df_consultas["valor"].sum() if not df_consultas.empty and "valor" in df_consultas else 0

    st.metric("Gasto Total", f"R$ {total_compras + total_consultas:.2f}")

    if not df_compras.empty:
        st.subheader("Compras de Medicamentos")
        cols = [col for col in ["data_compra", "nome_remedio", "valor"] if col in df_compras.columns]
        st.dataframe(df_compras[cols], use_container_width=True)

    if not df_consultas.empty:
        st.subheader("Consultas")
        cols = [col for col in ["data_consulta", "medico", "valor"] if col in df_consultas.columns]
        st.dataframe(df_consultas[cols], use_container_width=True)


def tela_cadastro() -> None:
    st.title("Cadastro")
    if not st.session_state.admin:
        st.warning("Acesse o modo ADM para cadastrar.")
        return

    tipo = st.selectbox("Tipo de Cadastro", ["Remedio", "Consulta"])
    with st.form("cadastro_novo"):
        if tipo == "Remedio":
            nome = st.text_input("Nome")
            qtd = st.number_input("Qtd Caixa", min_value=1, value=30, step=1)
            dose = st.number_input("Dose diaria", min_value=0.1, value=1.0, step=0.1)
            preco = st.number_input("Preco", min_value=0.0, value=0.0, step=0.01)
            precisa_receita = st.checkbox("Precisa de receita")

            if st.form_submit_button("Salvar Medicamento"):
                if not nome.strip():
                    st.error("Informe o nome do remedio.")
                    return

                ok_remedio = api_write(
                    "POST",
                    "remedios",
                    {
                        "nome": nome.strip(),
                        "qtd_total": int(qtd),
                        "dose_diaria": float(dose),
                        "preco": float(preco),
                        "precisa_receita": bool(precisa_receita),
                        "data_inicio": str(datetime.now().date()),
                    },
                )
                ok_compra = api_write(
                    "POST",
                    "compras",
                    {
                        "nome_remedio": nome.strip(),
                        "valor": float(preco),
                        "data_compra": str(datetime.now().date()),
                    },
                )

                if ok_remedio and ok_compra:
                    enviar_telegram(f"NOVO MEDICAMENTO: {nome.strip()}\n{int(qtd)} unidades")
                    st.success("Medicamento salvo com sucesso.")
                    time.sleep(1)
                    st.rerun()
        else:
            medico = st.text_input("Medico")
            valor = st.number_input("Valor", min_value=0.0, value=0.0, step=0.01)
            data_consulta = st.date_input("Data")

            if st.form_submit_button("Salvar Consulta"):
                if not medico.strip():
                    st.error("Informe o nome do medico.")
                    return

                if api_write(
                    "POST",
                    "consultas",
                    {
                        "medico": medico.strip(),
                        "valor": float(valor),
                        "data_consulta": str(data_consulta),
                    },
                ):
                    enviar_telegram(f"NOVA CONSULTA: {medico.strip()}\nValor: R$ {valor:.2f}")
                    st.success("Consulta salva com sucesso.")
                    time.sleep(1)
                    st.rerun()


def tela_remover() -> None:
    st.title("Remover")
    if not st.session_state.admin:
        st.warning("Acesse o modo ADM para remover.")
        return

    tabela = st.selectbox("Escolha a categoria", ["remedios", "consultas", "compras"])
    df = api_get(tabela)
    if df.empty:
        st.info("Nenhum item encontrado para remover.")
        return

    coluna_nome = "nome" if tabela == "remedios" else "medico" if tabela == "consultas" else "nome_remedio"
    if coluna_nome not in df.columns:
        st.error("A estrutura dessa tabela nao contem a coluna esperada.")
        return

    item = st.selectbox("Item para excluir", df[coluna_nome].astype(str).tolist())
    if st.button("Remover Permanente", type="primary"):
        item_id = df.loc[df[coluna_nome].astype(str) == item, "id"].iloc[0]
        if api_write("DELETE", f"{tabela}?id=eq.{item_id}"):
            st.success("Item removido com sucesso.")
            time.sleep(1)
            st.rerun()


def main() -> None:
    app_ready()
    init_state()
    render_css()
    menu = render_sidebar()

    if menu == "Estoque":
        tela_estoque()
    elif menu == "Historico Medico":
        tela_historico()
    elif menu == "Financeiro":
        tela_financeiro()
    elif menu == "Cadastro":
        tela_cadastro()
    elif menu == "Remover":
        tela_remover()


if __name__ == "__main__":
    main()
