import streamlit as st
from supabase import create_client, Client

# Configurações do Supabase (Substitua pelos seus dados se necessário)
URL_SUPABASE = "SUA_URL_AQUI"
CHAVE_SUPABASE = "SUA_CHAVE_AQUI"
supabase: Client = create_client(URL_SUPABASE, CHAVE_SUPABASE)

def main():
    st.set_page_config(page_title="Saúde na Veia - Controle de Medicamentos", layout="centered")
    st.title("💊 Controle de Medicamentos")

    # --- FORMULÁRIO DE CADASTRO ---
    with st.expander("Cadastrar Novo Remédio", expanded=True):
        with st.form("form_cadastro", clear_on_submit=True):
            nome = st.text_input("Nome do Medicamento")
            
            col1, col2 = st.columns(2)
            with col1:
                # Campo de Preço para Controle Financeiro
                preco = st.number_input("Preço de Custo (R$)", min_value=0.0, step=0.01, format="%.2f")
            with col2:
                # Campo de Categoria
                categoria = st.selectbox("Categoria", ["Analgésico", "Antibiótico", "Uso Contínuo", "Outros"])

            col3, col4 = st.columns(2)
            with col3:
                # Estoque atual
                estoque = st.number_input("Quantidade em Estoque", min_value=0, step=1)
            with col4:
                # Limite para o alerta do Telegram
                estoque_minimo = st.number_input("Aviso de Estoque Baixo (mínimo)", min_value=1, value=5)

            btn_cadastrar = st.form_submit_button("Salvar no Sistema")

            if btn_cadastrar:
                if nome:
                    data = {
                        "nome": nome,
                        "preco": preco,
                        "estoque": estoque,
                        "estoque_minimo": estoque_minimo,
                        "categoria": categoria
                    }
                    try:
                        supabase.table("remedios").insert(data).execute()
                        st.success(f"✅ {nome} cadastrado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
                else:
                    st.warning("Por favor, preencha o nome do medicamento.")

    # --- VISUALIZAÇÃO E CONTROLE ---
    st.subheader("Meus Medicamentos")
    
    try:
        response = supabase.table("remedios").select("*").order("nome").execute()
        remedios = response.data

        if remedios:
            for item in remedios:
                with st.container():
                    col_info, col_del = st.columns([4, 1])
                    
                    with col_info:
                        # Verifica se o estoque está baixo para mostrar um alerta visual
                        alerta = "⚠️" if item['estoque'] <= item['estoque_minimo'] else ""
                        st.write(f"**{item['nome']}** {alerta}")
                        st.caption(f"Preço: R$ {item['preco']:.2f} | Estoque: {item['estoque']} unidades | Cat: {item['categoria']}")
                    
                    with col_del:
                        # Botão de exclusão permanente (Banco de Dados e Controle Financeiro)
                        if st.button("Apagar", key=f"del_{item['id']}"):
                            supabase.table("remedios").delete().eq("id", item['id']).execute()
                            st.rerun()
                    st.divider()
        else:
            st.info("Nenhum remédio cadastrado ainda.")
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

if __name__ == "__main__":
    main()
