import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timedelta


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

st.set_page_config(page_title="Gestao Saude", page_icon="💊", layout="wide")


def init_state():
    st.session_state.setdefault("admin", False)
    st.session_state.setdefault("alertas_enviados", {})


def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem}, timeout=5)
    except requests.RequestException:
        pass


def tratar_datas(df):
    if df.empty:
        return df

    for col in ["data_inicio", "data_consulta", "data_compra"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


@st.cache_data(ttl=60)
def api_get(tabela):
    try:
        res = requests.get(
            f"{URL_SUPABASE}{tabela}?select=*&order=id.desc",
            headers=HEADERS,
            timeout=10,
        )
        res.raise_for_status()
        return tratar_datas(pd.DataFrame(res.json()))
    except requests.RequestException:
        st.warning(f"Nao foi possivel carregar a tabela {tabela}.")
        return pd.DataFrame()


def api_write(method, endpoint, payload=None):
    try:
        res = requests.request(
            method=method,
            url=f"{URL_SUPABASE}{endpoint}",
            headers=HEADERS,
            json=payload,
            timeout=10,
        )
        res.raise_for_status()
        api_get.clear()
        return True
    except requests.RequestException as e:
        st.error(f"Erro ao salvar no Supabase: {e}")
        return False


def calcular_estoque(remedio, hoje):
    data_inicio = remedio.get("data_inicio")
    qtd_total = int(remedio.get("qtd_total", 0) or 0)
    dose_diaria = float(remedio.get("dose_diaria", 0) or 0)

    if pd.isna(data_inicio):
        data_inicio = hoje

    dias_passados = max(0, (hoje.date() - data_inicio.date()).days)
    consumido = int(dias_passados * dose_diaria)
    estoque_atual = max(0, qtd_total - consumido)

    if dose_diaria > 0:
        dias_restantes = int(estoque_atual / dose_diaria)
    else:
        dias_restantes = 0

    data_fim = hoje + timedelta(days=dias_restantes)
    return estoque_atual, dias_restantes, data_fim


def alerta_estoque(remedio, estoque_atual, dias_restantes, data_fim):
    if dias_restantes >= 7:
        return

    alerta_id = f"{remedio['id']}-{data_fim.strftime('%Y-%m-%d')}"
    if alerta_id in st.session_state.alertas_enviados:
        return

    msg = (
        f"ALERTA: {remedio['nome']} acabando!\n\n"
        f"Estoque: {estoque_atual} un.\n"
        f"Restam {dias_restantes} dias.\n"
        f"Acaba em: {data_fim.strftime('%d/%m/%Y')}"
    )
    enviar_telegram(msg)
    st.session_state.alertas_enviados[alerta_id] = True


def render_css():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #f4f8ff 0%, #eaf2ff 100%) !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #dcecff 0%, #cfe3fb 100%) !important;
            border-right: 1px solid #b4cfee;
        }

        [data-testid="stSidebar"] * {
            color: #12324a !important;
        }

        [data-testid="stSidebar"] hr {
            border-color: #a8c8ea !important;
        }

        .med-card {
            background: #ffffff;
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 18px;
            border-left: 10px solid #5b9dff;
            box-shadow: 0 8px 24px rgba(44, 101, 163, 0.10);
        }

        .med-card.alerta-receita {
            border-left: 10px solid #ff8a3d;
            background: linear-gradient(180deg, #fff7ef 0%, #ffeddc 100%);
        }

        .titulo-remedio {
            font-size: 1.5rem;
            font-weight: 800;
            color: #12324a;
            margin-bottom: 8px;
        }

        .linha-info {
            font-size: 1.04rem;
            color: #1c425f;
            margin-bottom: 8px;
        }

        .linha-alerta {
            font-size: 1.08rem;
            font-weight: 700;
            color: #c0392b;
            margin-top: 10px;
        }

        .linha-ok {
            font-size: 1.08rem;
            font-weight: 700;
            color: #1e8449;
            margin-top: 10px;
        }

        div.stButton > button {
            width: 100%;
            border-radius: 12px;
            background: linear-gradient(180deg, #69abff 0%, #4b91f1 100%) !important;
            color: #ffffff !important;
            font-weight: 700;
            border: none !important;
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="base-input"] > div,
        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        .stSelectbox > div > div {
            background-color: #ffffff !important;
            color: #12324a !important;
            border-radius: 12px !important;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='text-align:center;'>Gestao Saude</h2>", unsafe_allow_html=True)
        st.markdown("---")

        if not st.session_state.admin:
            senha = st.text_input("Senha ADM", type="password")
            if st.button("Liberar"):
                if senha == ADMIN_PASSWORD:
                    st.session_state.admin = True
                    st.rerun()
                else:
                    st.error("Senha invalida.")
        else:
            st.success("Modo editor ativo")
            if st.button("Sair ADM"):
                st.session_state.admin = False
                st.rerun()

        st.markdown("---")
        menu = st.radio(
            "Navegacao",
            ["Estoque", "Historico Medico", "Financeiro", "Cadastro", "Remover"]
        )
        return menu


def tela_estoque():
    st.title("Controle de Remedios")
    df = api_get("remedios")

    if df.empty:
        st.info("Nenhum remedio cadastrado.")
        return

    col1, col2 = st.columns([1.2, 1])
    with col1:
        filtro_receita = st.selectbox(
            "Filtrar por receita",
            ["Todos", "So com receita", "So sem receita"]
        )
    with col2:
        mostrar_alertas = st.checkbox("Mostrar so os que estao acabando")

    hoje = datetime.now()
    exibidos = 0

    for _, remedio in df.iterrows():
        estoque_atual, dias_restantes, data_fim = calcular_estoque(remedio, hoje)
        alerta_estoque(remedio, estoque_atual, dias_restantes, data_fim)

        precisa_receita = bool(remedio.get("precisa_receita", False))

        if filtro_receita == "So com receita" and not precisa_receita:
            continue
        if filtro_receita == "So sem receita" and precisa_receita:
            continue
        if mostrar_alertas and dias_restantes >= 7:
            continue

        exibidos += 1
        precisa_receita_texto = "Sim" if precisa_receita else "Nao"
        classe_card = "med-card alerta-receita" if precisa_receita and dias_restantes < 7 else "med-card"
        classe_data = "linha-alerta" if dias_restantes < 7 else "linha-ok"

        alerta_receita_html = ""
        if precisa_receita and dias_restantes < 7:
            alerta_receita_html = """
                <div class="linha-alerta">
                    Atencao: este remedio precisa de receita e esta perto de acabar.
                </div>
            """

        st.markdown(
            f"""
            <div class="{classe_card}">
                <div class="titulo-remedio">{str(remedio['nome']).upper()}</div>
                <div class="linha-info">Estoque: <b>{estoque_atual} un.</b> | Dose: <b>{remedio['dose_diaria']} p/ dia</b></div>
                <div class="linha-info">Precisa de receita: <b>{precisa_receita_texto}</b></div>
                {alerta_receita_html}
                <div class="{classe_data}">Acaba em: <b>{data_fim.strftime('%d/%m/%Y')}</b> ({dias_restantes} dias)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.admin:
            with st.expander(f"Repor {remedio['nome']}"):
                with st.form(f"reposicao_{remedio['id']}"):
                    qtd_comprada = st.number_input(
                        "Quantidade comprada agora",
                        min_value=1,
                        value=30,
                        step=1,
                    )
                    preco_compra = st.number_input(
                        "Preco pago nesta compra",
                        min_value=0.0,
                        value=float(remedio.get("preco", 0.0) or 0.0),
                        step=0.01,
                    )
                    precisa_receita_novo = st.checkbox(
                        "Precisa de receita",
                        value=precisa_receita,
                        key=f"receita_{remedio['id']}",
                    )

                    if st.form_submit_button("Confirmar reposicao"):
                        total_novo = estoque_atual + int(qtd_comprada)

                        ok_remedio = api_write(
                            "PATCH",
                            f"remedios?id=eq.{remedio['id']}",
                            {
                                "qtd_total": total_novo,
                                "preco": float(preco_compra),
                                "precisa_receita": bool(precisa_receita_novo),
                                "data_inicio": str(hoje.date()),
                            },
                        )

                        ok_compra = api_write(
                            "POST",
                            "compras",
                            {
                                "nome_remedio": remedio["nome"],
                                "valor": float(preco_compra),
                                "data_compra": str(hoje.date()),
                            },
                        )

                        if ok_remedio and ok_compra:
                            enviar_telegram(
                                f"REPOSICAO: {remedio['nome']}\n"
                                f"Qtd comprada: {int(qtd_comprada)}\n"
                                f"Novo estoque: {total_novo} un.\n"
                                f"Valor pago: R$ {preco_compra:.2f}"
                            )
                            st.success("Reposicao registrada com sucesso.")
                            time.sleep(1)
                            st.rerun()

    if exibidos == 0:
        st.info("Nenhum remedio encontrado com esse filtro.")


def tela_historico():
    st.title("Consultas Realizadas")
    df = api_get("consultas")

    if df.empty:
        st.info("Nenhuma consulta cadastrada.")
        return

    for _, consulta in df.iterrows():
        data = consulta.get("data_consulta")
        data_fmt = data.strftime("%d/%m/%Y") if pd.notna(data) else "Sem data"
        valor = float(consulta.get("valor", 0) or 0)
        medico = consulta.get("medico", "Nao informado")

        st.markdown(
            f"""
            <div class="med-card">
                <div class="titulo-remedio">{medico}</div>
                <div class="linha-info">Data: <b>{data_fmt}</b></div>
                <div class="linha-info">Valor: <b>R$ {valor:.2f}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def tela_financeiro():
    st.title("Resumo Financeiro")

    df_compras = api_get("compras")
    df_consultas = api_get("consultas")

    total_remedios = df_compras["valor"].sum() if not df_compras.empty and "valor" in df_compras.columns else 0
    total_consultas = df_consultas["valor"].sum() if not df_consultas.empty and "valor" in df_consultas.columns else 0
    total_geral = total_remedios + total_consultas

    c1, c2, c3 = st.columns(3)
    c1.metric("Gasto com remedios", f"R$ {total_remedios:.2f}")
    c2.metric("Gasto com consultas", f"R$ {total_consultas:.2f}")
    c3.metric("Gasto total", f"R$ {total_geral:.2f}")

    if not df_compras.empty:
        st.subheader("Compras de remedios")
        cols = [c for c in ["data_compra", "nome_remedio", "valor"] if c in df_compras.columns]
        st.dataframe(df_compras[cols], use_container_width=True)

    if not df_consultas.empty:
        st.subheader("Consultas")
        cols = [c for c in ["data_consulta", "medico", "valor"] if c in df_consultas.columns]
        st.dataframe(df_consultas[cols], use_container_width=True)


def tela_cadastro():
    st.title("Cadastro")

    if not st.session_state.admin:
        st.warning("Acesse o modo ADM para cadastrar.")
        return

    tipo = st.selectbox("Tipo de cadastro", ["Remedio", "Consulta"])

    with st.form("cadastro_novo"):
        if tipo == "Remedio":
            nome = st.text_input("Nome")
            qtd = st.number_input("Quantidade da caixa", min_value=1, value=30, step=1)
            dose = st.number_input("Dose diaria", min_value=0.1, value=1.0, step=0.1)
            preco = st.number_input("Preco", min_value=0.0, value=0.0, step=0.01)
            precisa_receita = st.checkbox("Precisa de receita")

            if st.form_submit_button("Salvar medicamento"):
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
                    enviar_telegram(
                        f"NOVO MEDICAMENTO: {nome.strip()}\n"
                        f"Quantidade: {int(qtd)}\n"
                        f"Preco: R$ {preco:.2f}"
                    )
                    st.success("Medicamento salvo com sucesso.")
                    time.sleep(1)
                    st.rerun()

        else:
            medico = st.text_input("Medico")
            valor = st.number_input("Valor", min_value=0.0, value=0.0, step=0.01)
            data_consulta = st.date_input("Data")

            if st.form_submit_button("Salvar consulta"):
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
                    enviar_telegram(
                        f"NOVA CONSULTA: {medico.strip()}\n"
                        f"Valor: R$ {valor:.2f}"
                    )
                    st.success("Consulta salva com sucesso.")
                    time.sleep(1)
                    st.rerun()


def tela_remover():
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
        st.error("Nao encontrei a coluna principal dessa tabela.")
        return

    item = st.selectbox("Item para excluir", df[coluna_nome].astype(str).tolist())

    if st.button("Remover permanente"):
        item_id = df.loc[df[coluna_nome].astype(str) == item, "id"].iloc[0]
        if api_write("DELETE", f"{tabela}?id=eq.{item_id}"):
            st.success("Item removido com sucesso.")
            time.sleep(1)
            st.rerun()


def main():
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
