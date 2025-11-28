import streamlit as st
import pandas as pd
import altair as alt
from db import get_general_analytics, get_price_history

st.set_page_config(page_title="Análise de Preços", layout="wide")
st.title("📊 Análise de Preços de Mercado")

st.markdown("""
Aqui você acompanha a variação de preços dos seus produtos padronizados.
""")

# Carregar dados
df = get_general_analytics()

if df.empty:
    st.warning("Nenhum dado encontrado. Certifique-se de ter importado notas e realizado a padronização (De-Para).")
else:
    # Filtros
    all_cats = df["categoria"].dropna().unique().tolist()
    selected_cats = st.multiselect("Filtrar por Categoria", options=all_cats, default=all_cats)
    
    if selected_cats:
        df_filtered = df[df["categoria"].isin(selected_cats)]
    else:
        df_filtered = df

    # Exibição Tabela Principal
    st.dataframe(
        df_filtered,
        column_config={
            "nome_padrao": "Produto",
            "categoria": "Categoria",
            "media_7d": st.column_config.NumberColumn("Média (7d)", format="R$ %.2f"),
            "media_30d": st.column_config.NumberColumn("Média (30d)", format="R$ %.2f"),
            "preco_min": st.column_config.NumberColumn("Mínimo", format="R$ %.2f"),
            "preco_max": st.column_config.NumberColumn("Máximo", format="R$ %.2f"),
            "local_mais_barato": "Onde Comprar (Barato)",
            "data_melhor_preco": st.column_config.DateColumn("Data (Melhor Preço)")
        },
        hide_index=True,
        use_container_width=True
    )

    st.divider()

    # Detalhe por Produto (Gráfico)
    st.subheader("📈 Histórico de Preço por Produto")
    
    produtos = df_filtered["nome_padrao"].unique()
    prod_selecionado = st.selectbox("Selecione um produto para ver o histórico:", options=produtos)

    if prod_selecionado:
        df_history = get_price_history(prod_selecionado)
        
        if not df_history.empty:
            # Gráfico de Linha
            chart = alt.Chart(df_history).mark_line(point=True).encode(
                x=alt.X('emissao', title='Data da Compra'),
                y=alt.Y('valor_unitario', title='Preço (R$)'),
                tooltip=['emissao', 'valor_unitario', 'estabelecimento']
            ).properties(
                height=400
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)
            
            # Mostrar tabela de histórico também
            st.caption("Últimas compras deste item:")
            st.dataframe(df_history.sort_values("emissao", ascending=False).head(10), hide_index=True)
