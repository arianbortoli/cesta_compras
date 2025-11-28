import streamlit as st
import pandas as pd
from db import (
    get_unmapped_items, get_categories, create_category,
    get_catalog_items, create_catalog_item, link_items
)

st.set_page_config(page_title="Padronização de Produtos", layout="wide")
st.title("🏷️ Padronização de Produtos (De-Para)")

# --- Abas para separar cadastro de vinculação ---
tab1, tab2 = st.tabs(["🔗 Vincular Produtos", "📝 Cadastrar Padrões"])

# ---------------------------------------------------------
# ABA 1: VINCULAR (O fluxo principal de trabalho)
# ---------------------------------------------------------
with tab1:
    st.header("Vincular itens da nota a produtos padrão")
    
    # 1. Buscar itens pendentes
    unmapped = get_unmapped_items()
    
    if not unmapped:
        st.success("🎉 Todos os itens já foram padronizados!")
    else:
        st.write(f"Existem **{len(unmapped)}** descrições de produtos pendentes de padronização.")
        
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.subheader("1. Selecione os itens 'sujos'")
            # Multiselect com filtro
            selected_origins = st.multiselect(
                "Selecione um ou mais itens originais:",
                options=unmapped
            )
            
            if selected_origins:
                st.info(f"{len(selected_origins)} itens selecionados.")

        with col_right:
            st.subheader("2. Escolha o produto padrão")
            
            # Carregar catálogo
            df_catalog = get_catalog_items()
            
            if df_catalog.empty:
                st.warning("Nenhum produto padrão cadastrado. Vá na aba 'Cadastrar Padrões' primeiro.")
            else:
                # Criar lista formatada para o selectbox
                # Ex: "Leite Integral (UN) - [Laticínios]"
                df_catalog["display_name"] = df_catalog.apply(
                    lambda x: f"{x['nome_padrao']} ({x['unidade_padrao'] or '-'}) | {x['categoria'] or 'Sem Categoria'}", 
                    axis=1
                )
                
                # Dicionário para mapear display -> id
                catalog_map = dict(zip(df_catalog["display_name"], df_catalog["id"]))
                
                selected_target_name = st.selectbox(
                    "Selecione o produto destino:",
                    options=df_catalog["display_name"]
                )
                
                if selected_target_name and selected_origins:
                    target_id = catalog_map[selected_target_name]
                    
                    if st.button("🔗 Vincular Selecionados"):
                        try:
                            link_items(selected_origins, target_id)
                            st.success("Vínculo realizado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao vincular: {e}")

# ---------------------------------------------------------
# ABA 2: CADASTROS (Categorias e Produtos Padrão)
# ---------------------------------------------------------
with tab2:
    col1, col2 = st.columns(2)
    
    # --- Cadastro de Categorias ---
    with col1:
        st.subheader("Nova Categoria")
        new_cat_name = st.text_input("Nome da Categoria (ex: Açougue)")
        if st.button("Salvar Categoria"):
            if new_cat_name:
                create_category(new_cat_name)
                st.success(f"Categoria '{new_cat_name}' criada!")
                st.rerun()
            else:
                st.error("Digite um nome.")
                
        st.divider()
        st.caption("Categorias Existentes:")
        df_cats = get_categories()
        if not df_cats.empty:
            st.dataframe(df_cats, hide_index=True)

    # --- Cadastro de Produtos Padrão ---
    with col2:
        st.subheader("Novo Produto Padrão")
        
        df_cats = get_categories()
        if df_cats.empty:
            st.warning("Crie categorias antes de criar produtos.")
        else:
            cat_options = dict(zip(df_cats["nome"], df_cats["id"]))
            selected_cat = st.selectbox("Categoria", options=cat_options.keys())
            
            prod_name = st.text_input("Nome Padrão (ex: Picanha Bovina)")
            prod_unit = st.text_input("Unidade Padrão (ex: KG, UN, CX)")
            
            if st.button("Salvar Produto"):
                if prod_name and selected_cat:
                    cat_id = cat_options[selected_cat]
                    create_catalog_item(prod_name, prod_unit, cat_id)
                    st.success(f"Produto '{prod_name}' criado!")
                    st.rerun()
                else:
                    st.error("Preencha nome e categoria.")
        
        st.divider()
        st.caption("Produtos Cadastrados:")
        df_prods = get_catalog_items()
        if not df_prods.empty:
            st.dataframe(df_prods[["nome_padrao", "unidade_padrao", "categoria"]], hide_index=True)

