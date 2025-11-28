
import streamlit as st
from db import fetch_table
from nf_requester import nf_requester
from parsers import Parser
from mongo import my_mongo
import time

st.title("☁️ Importar para MongoDB")
st.markdown("Este processo busca os dados detalhados das NFC-e da SEFAZ-RS e armazena no MongoDB.")

# Botão para iniciar o processo
if st.button("🚀 Importar notas do PostgreSQL para o MongoDB"):
    try:
        # Busca chaves de acesso no PostgreSQL
        df = fetch_table("nfe_headers")
        chaves = df["chave_acesso"].dropna().unique()

        st.write(f"🔎 {len(chaves)} chaves encontradas.")

        # Instanciar classes
        rq = nf_requester()
        parser = Parser()
        mongo = my_mongo()
        mongo.set_collection("nfe_detalhes")

        total_importadas = 0
        total_existentes = 0
        total_erros = 0
        skipped = 0

        progress_bar = st.progress(0)  # cria a barra antes do loop
        status = st.empty()

        with st.spinner("Buscando e salvando dados..."):
            for idx, chave in enumerate(chaves):
                try:
                    tipo_doc = df.loc[df["chave_acesso"] == chave, "tipo_doc"].values[0]

                    if "Nota Fiscal Eletrônica" in tipo_doc:
                        st.info(f"🔁 Pulando NFe (não suportada): {chave}")
                        skipped += 1
                        continue

                    chave_limpa = chave.replace(" ", "").strip()
                    xhtml = rq.request_nfce(chave_limpa)
                    dados_json = parser.parse_nfce(xhtml)
                    resultado = mongo.insert_one(dados_json)

                    if resultado is True:
                        total_importadas += 1
                    elif resultado is False:
                        total_existentes += 1
                    else:
                        total_erros += 1
                        st.warning(f"Erro ao inserir chave {chave}: {resultado}")

                    progress_bar.progress((idx + 1) / len(chaves))
                    status.write(f"🔁 Processando chave {idx+1} de {len(chaves)}")
                    time.sleep(1.5)

                except Exception as e:
                    total_erros += 1
                    st.error(f"Erro na chave {chave}: {e}")

        st.success(f"✅ Importação finalizada:")
        st.markdown(f"- **Novas inserções:** {total_importadas}")
        st.markdown(f"- **Já existentes:** {total_existentes}")
        st.markdown(f"- **Com erro:** {total_erros}")
        st.markdown(f"- **Puladas (NFe):** {skipped}")

    except Exception as e:
        st.error(f"Erro geral: {e}")
