import streamlit as st
from nf_requester import nf_requester
from parsers import Parser
from mongo import my_mongo
import json

st.title("🧪 Testar Importação de Nota Fiscal")
st.markdown("Digite a **chave de acesso** e selecione o **tipo de documento** para consultar e importar para o MongoDB.")

# Inputs do usuário
chave = st.text_input("Chave de Acesso", max_chars=60)
tipo_doc = st.selectbox("Tipo de Documento", ["Nota Fiscal de Consumidor Eletrônica", "Nota Fiscal Eletrônica"])

if st.button("Consultar e Importar"):
    
        try:
            chave_limpa = chave.replace(" ", "").strip()
            rq = nf_requester()

            # Consulta baseada no tipo
            if "Consumidor" in tipo_doc:
                st.info("🔍 Consultando NFC-e (RS)...")
                xhtml = rq.request_nfce(chave_limpa)
            else:
                st.info("🔍 Consultando NFe (nacional)...")
                xhtml = rq.request_nfe_resumo(chave_limpa)

            st.expander("📄 Ver HTML bruto").code(xhtml[:2000])

            st.success("✅ Consulta realizada com sucesso. Iniciando o parser...")

            parser = Parser()
            dados_json = parser.parse_nfce(xhtml)  # Por enquanto usamos o mesmo parser

            st.subheader("🧾 Dados extraídos:")
            st.json(dados_json)

            mongo = my_mongo()
            mongo.set_collection("nfe_detalhes")
            resultado = mongo.insert_one(dados_json)

            if resultado is True:
                st.success("🎉 Nota fiscal importada com sucesso no MongoDB!")
            elif resultado is False:
                st.info("ℹ️ Essa nota já estava no banco de dados.")
            else:
                st.error(f"Erro ao inserir no MongoDB: {resultado}")

        except Exception as e:
            st.error(f"❌ Erro ao processar a nota: {e}")
