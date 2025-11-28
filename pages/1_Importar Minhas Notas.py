import streamlit as st
import pandas as pd
from db import insert_new_nfes

# 🔧 Funções locais
def clean_columns(df):
    """Remove a primeira coluna se estiver vazia."""
    if df.columns[0] == "" or df.columns[0].lower().startswith("unnamed"):
        df.drop(df.columns[0], axis=1, inplace=True)
    return df

def transform_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Renomeia as colunas
    df.columns = [
        "munic", "razao_social", "emissao", "numero", "tipo_doc",
        "chave_acesso", "valor_em_brl", "data_registro",
        "tipo_operacao", "situacao_docto"
    ]

    # Limpa e converte o valor
    df["valor_em_brl"] = (
        df["valor_em_brl"]
        .replace("R\$", "", regex=True)
        .str.replace(".", "", regex=False)   # remove separador de milhar
        .str.replace(",", ".", regex=False)  # troca separador decimal
        .astype(float)
    )

    # Converte datas
    df["emissao"] = pd.to_datetime(df["emissao"], format="%d/%m/%y", errors="coerce").dt.date
    df["data_registro"] = pd.to_datetime(df["data_registro"], format="%d/%m/%y", errors="coerce").dt.date

    # Opcional: avisa se houver datas inválidas
    if df["emissao"].isna().any() or df["data_registro"].isna().any():
        st.warning("⚠️ Algumas datas não foram convertidas corretamente. Verifique o formato (ex: 21/07/25).")

    return df


# 🚀 Interface do Streamlit
st.title("📥 Importar Minhas Notas")
st.markdown("Envie o arquivo CSV com suas notas fiscais para armazenar no sistema.")


uploaded_file = st.file_uploader("Selecione um arquivo CSV", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df = clean_columns(df)
        df = transform_dataframe(df)

        st.subheader("Pré-visualização dos dados:")
        st.dataframe(df)

        with st.spinner("Verificando e enviando dados para o banco..."):
            inserted_count = insert_new_nfes(df)

        if inserted_count > 0:
            st.success(f"{inserted_count} novas notas foram adicionadas com sucesso.")
        else:
            st.info("Nenhuma nova nota foi inserida. Todas já existiam no banco.")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
