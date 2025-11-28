import streamlit as st
from mongo import my_mongo
from db import get_or_create_estabelecimento, get_nfe_id_by_chave, inserir_itens_nf

st.set_page_config(page_title="Importar Estabelecimentos e Itens", layout="wide")
st.title("📄 Importar Estabelecimentos e Itens do MongoDB para o PostgreSQL")

mongo = my_mongo()
mongo.set_collection("nfe_detalhes")

# Seção 1 – Mostrar e Importar Estabelecimentos
st.header("🏢 Estabelecimentos")
estabs = mongo.get_unique_estabelecimento()
st.write(f"Total de estabelecimentos encontrados: {len(estabs)}")
st.dataframe(estabs)

if st.button("📥 Importar Estabelecimentos"):
    total = len(estabs)
    inseridos = 0
    
    progress = st.progress(0, text="Iniciando importação de estabelecimentos...")
    status = st.empty()

    for i, est in enumerate(estabs):
        id_estab = get_or_create_estabelecimento({
            "nome": est["_id"]["nome"],
            "endereco": est["_id"]["endereco"],
            "cnpj": est["_id"]["cnpj"],
            "inscricao_estadual": est["_id"].get("inscricao_estadual", "")
        })
        inseridos += 1 if id_estab else 0
        progress.progress((i + 1) / total, text=f"{i+1}/{total} estabelecimentos processados")
        status.write(f"🔁 Processando estabelcimento {i+1} de {total}")

    st.success(f"✔️ {inseridos} estabelecimentos inseridos/validados no PostgreSQL.")
# Seção 2 – Mostrar e Importar Itens por Compra
st.header("🧾 Itens por Compra")
itens = mongo.get_items_por_compras()
st.write(f"Total de registros de itens encontrados: {len(itens)}")
st.dataframe(itens[:100])  # Mostra só os primeiros 100 para não travar

if st.button("📥 Importar Itens por Compra"):
    processados = 0
    erros = 0

    progress = st.progress(0, text="Iniciando importação dos itens de compras...")
    status = st.empty()

    for i, item in enumerate(itens):
        try:
            chave = item["chave"].replace(" ", "")
            id_nfe = get_nfe_id_by_chave(chave)
            if not id_nfe:
                st.warning(f"Nota não encontrada: {chave}")
                continue
            # Garantir que todos os campos estejam como string
            item_convertido = {
                "codigo": str(item.get("codigo", "")).strip(),
                "descricao": str(item.get("descricao", "")).strip(),
                "quantidade": str(item.get("quantidade", "")).replace(",", "."),
                "unidade": str(item.get("unidade", "un")),
                "valor_unitario": str(item.get("valor_unitario", "")).replace(",", "."),
                "valor_total": str(item.get("valor_total", "")).replace(",", ".")
            }

            inserir_itens_nf(id_nfe, [item_convertido])
            processados += 1
            
        except Exception as e:
            st.error(f"Erro ao processar {item['chave']}: {e}")
            erros += 1
        progress.progress((i + 1) / len(itens), text=f"{i+1}/{len(itens)} itens processados")
        status.write(f"🔁 Processando item {i+1} de {len(itens)}")

    st.success(f"✔️ Itens processados: {processados} | ❌ Erros: {erros}")
