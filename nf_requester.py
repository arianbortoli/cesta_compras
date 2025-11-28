import requests
import base64

class nf_requester():
    def request_nfce(self, NFeKey):

        url = f"https://www.sefaz.rs.gov.br/ASP/AAE_ROOT/NFE/SAT-WEB-NFE-NFC_2.asp?chaveNFe={NFeKey}&HML=false&Action=Avançar"

        payload = {}
        headers = {
            'Cookie': 'ticketSessionProviderSS=700b53c122bb41ee88bcd4a715a9a075; ASPSESSIONIDSUTAQTTA=DOHBPFACHHHDKJOPCEMIANDK; AffinitySefaz=c61190ec9eb1b57a94adfa63e4d1b9a40a8d78d52e453413a24e381e9f07bc6a'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        return response.text

    def request_nfe_resumo(self, NFeKey):
        # Gera o código base64 da chave como exige o site da Receita
        
        chave_limpa = NFeKey.replace(" ", "").strip()
        chave_encoded = base64.b64encode(chave_limpa.encode("utf-8")).decode("utf-8")

        url = f"https://www.nfe.fazenda.gov.br/portal/consultaImpressao.aspx?tipoConsulta=resumo&lp={chave_encoded}"

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(url, headers=headers)
        return response.text

    def login_nfg(self):

        url = "https://nfg.sefaz.rs.gov.br/Login/LoginNfg.aspx"
        