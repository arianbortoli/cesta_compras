from bs4 import BeautifulSoup
import json
import re

class Parser():

    def parse_nfce(self, xhtml):

        # Analisar o XHTML
        soup = BeautifulSoup(xhtml, 'html.parser')

        # Extrair os dados relevantes do XHTML
        dados = {}

        # Extrair informações do estabelecimento
        estabelecimento = soup.find("td", class_="borda-pontilhada-botton")
        if estabelecimento:
            nome = estabelecimento.find("td", class_="NFCCabecalho_SubTitulo")
            endereco = estabelecimento.find_all("td", class_="NFCCabecalho_SubTitulo1")[1]

            endereco_texto = endereco.text.replace("\n", "").strip()
            endereco_texto_sem_espacos = ' '.join(endereco_texto.split())
                
            if nome and endereco:
                dados["estabelecimento"] = {
                    "nome": nome.text.strip(),
                    "endereco": endereco_texto_sem_espacos
                }

            # Agora, vamos buscar o CNPJ e a inscrição estadual
            cnpj_inscricao = estabelecimento.find("td", class_="NFCCabecalho_SubTitulo1").text.strip()
            linhas = cnpj_inscricao.split('\n')
            dados["estabelecimento"]["cnpj"] = linhas[1].strip()
            dados["estabelecimento"]["inscricao_estadual"] = linhas[2].strip().replace("Inscri��o Estadual: ", "").replace("Inscrição Estadual: ", "")


        emissao = soup.find_all('td', class_="NFCCabecalho_SubTitulo")[2]
        chave = soup.find_all('td', class_="NFCCabecalho_SubTitulo")[5]
        if emissao:
            dados["documento"] = {
                "data_emissao": re.split('Data de Emiss�o: |Data de Emissão: ', emissao.text)[-1],
                "chave": chave.text.strip().replace(" ", "")
            }

        # Extrair itens da NFC-e
        itens_nfce = soup.find_all("table", class_="NFCCabecalho")[3]
        if itens_nfce:
            dados["itens_nfce"] = []
            for item in itens_nfce.find_all("tr")[1:]:
                dados_item = {
                    "codigo": item.find_all("td")[0].text.strip(),
                    "descricao": item.find_all("td")[1].text.strip(),
                    "quantidade": item.find_all("td")[2].text.strip(),
                    "unidade": item.find_all("td")[3].text.strip(),
                    "valor_unitario": item.find_all("td")[4].text.strip(),
                    "valor_total": item.find_all("td")[5].text.strip()
                }
                dados["itens_nfce"].append(dados_item)

        # Extrair informações de pagamento
        pagamento = soup.find_all("table", class_="NFCCabecalho")[4]
        if pagamento:
            dados["pagamento"] = {
                "forma_pagamento": pagamento.find_all("td", class_="NFCDetalhe_Item")[6].text.strip(),
                "valor_pago": pagamento.find_all("td", class_="NFCDetalhe_Item")[7].text.strip(),
                "desconto": pagamento.find_all("td", class_="NFCDetalhe_Item")[3].text.strip()
            }

        # Converter para JSON
        json_data = json.dumps(dados, ensure_ascii=False, indent=4)

        return dados