import streamlit as st
from db import fetch_table
import pandas as pd

st.set_page_config(page_title="Visualizar Dados", layout="wide")
st.title("📊 Visualizar Dados do Banco de Dados")
st.markdown("Veja os dados atuais das tabelas `estabelecimentos` e `itens_nf`.")

aba = st.radio("Escolha a tabela para visualizar:", ["Estabelecimentos", "Itens das Notas"])

if aba == "Estabelecimentos":
    try:
        df = fetch_table("estabelecimentos")
        st.subheader(f"📍 Estabelecimentos ({len(df)} registros)")
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao carregar estabelecimentos: {e}")

elif aba == "Itens das Notas":
    try:
        df = fetch_table("itens_nf")
        st.subheader(f"🧾 Itens das Notas Fiscais ({len(df)} registros)")
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao carregar itens: {e}")
