import streamlit as st
import pandas as pd
from db import fetch_table

st.title("📄 Minhas Notas Fiscais")
st.markdown("Aqui estão todas as notas fiscais já importadas.")

# Tenta carregar os dados do banco
try:
    df = fetch_table("nfe_headers")

    if df.empty:
        st.info("Nenhuma nota fiscal foi encontrada no banco de dados ainda.")
    else:
        # Ordenar pela data de registro (ou de emissão, se preferir)
        df = df.sort_values(by="data_registro", ascending=False)

        # Exibir tabela
        st.dataframe(df, use_container_width=True)

        # Mostrar total de notas e total em reais
        st.markdown(f"**Total de notas:** {len(df)}")
        st.markdown(f"**Valor total:** R$ {df['valor_em_brl'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

except Exception as e:
    st.error(f"Erro ao carregar notas: {e}")
