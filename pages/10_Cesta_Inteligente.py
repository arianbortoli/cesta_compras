import streamlit as st
import pandas as pd
from db import get_catalog_items, calculate_basket_best_place

st.set_page_config(page_title="Cesta Inteligente", layout="wide")
st.title("🛒 Cesta Inteligente")

st.markdown("""
Monte sua lista de compras e descubra onde sai mais barato comprar todos os itens, 
com base no último preço praticado por cada mercado.
""")

# 1. Seleção de Produtos
df_catalog = get_catalog_items()

if df_catalog.empty:
    st.warning("Nenhum produto padronizado encontrado. Vá para a página de Padronização.")
else:
    # Criar map de ID -> Nome
    product_options = {row['nome_padrao']: row['id'] for _, row in df_catalog.iterrows()}
    
    selected_names = st.multiselect(
        "Quais produtos você quer comprar?",
        options=list(product_options.keys())
    )
    
    if selected_names:
        selected_ids = [product_options[name] for name in selected_names]
        
        if st.button("🔍 Calcular Melhor Lugar"):
            with st.spinner("Analisando preços históricos..."):
                df_result = calculate_basket_best_place(selected_ids)
            
            if df_result.empty:
                st.warning("Não encontrei histórico de preços para esses produtos em nenhum mercado comum.")
            else:
                st.subheader("🏆 Ranking de Mercados")
                
                # Destacar o melhor
                best = df_result.iloc[0]
                total_items = len(selected_ids)
                found_items = best['itens_encontrados']
                
                if found_items == total_items:
                    st.success(f"O melhor lugar é **{best['estab_nome']}**! Valor total estimado: **R$ {best['total_estimado']:.2f}**")
                else:
                    st.info(f"O melhor lugar parcial é **{best['estab_nome']}**, mas ele só tem {found_items} dos {total_items} itens.")

                st.dataframe(
                    df_result,
                    column_config={
                        "estab_nome": "Mercado",
                        "itens_encontrados": "Itens Encontrados",
                        "total_estimado": st.column_config.NumberColumn("Total Estimado", format="R$ %.2f"),
                        "detalhes": "Preços Considerados"
                    },
                    hide_index=True,
                    use_container_width=True
                )

