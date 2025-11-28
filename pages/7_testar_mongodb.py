import streamlit as st
import pandas as pd
from mongo import my_mongo

st.set_page_config(page_title="Testar MongoDB", layout="wide")

st.title("🔍 Testar Dados do MongoDB")

mongo = my_mongo()
mongo.set_collection("nfe_detalhes")

# ----- Estabelecimentos únicos -----
st.header("🏪 Estabelecimentos Únicos")

estabs = mongo.get_unique_estabelecimento()
if estabs:
    estabs_df = pd.DataFrame([e['_id'] for e in estabs])
    st.dataframe(estabs_df, use_container_width=True)
else:
    st.warning("Nenhum estabelecimento encontrado.")

# ----- Itens por compras -----
st.header("🛒 Itens por Compras")

itens = mongo.get_items_por_compras()
if itens:
    itens_df = pd.DataFrame(itens)
    st.dataframe(itens_df, use_container_width=True)
else:
    st.warning("Nenhum item encontrado.")
