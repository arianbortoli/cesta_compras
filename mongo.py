# Importe a biblioteca pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
load_dotenv()


class my_mongo():
    client = ''
    db = ''
    collection = ''

    def __init__(self):
        self.connect()

    def connect(self):
        uri = os.getenv("URI_MONGO", "mongodb+srv://"),
        # Create a new client and connect to the server
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        # Send a ping to confirm a successful connection
        # Acesse o banco de dados desejado
        self.db = self.client['notas_fiscais']

    def set_collection(self, collection):
        self.collection = self.db[collection]

    def insert_one(self, json=None):
        
        # Check if a document with the same chave already exists
        existing_document = self.collection.find_one({'documento.chave': json["documento"]["chave"]})

        # If no matching document is found, insert the new document
        if existing_document is None:
            try:
                self.collection.insert_one(json)
                return True
            except Exception as e:
                return e
        else:
            return False

    def insert_many(self, data=None):
        for item in data:
            self.insert_one(item)

    def remove_duplicate(self):

        field_to_check = "documento.chave"

        # Define the criteria for identifying duplicates
        pipeline = [
            {"$group": {"_id": f"${field_to_check}", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}}
        ]

        # Find duplicates based on the criteria
        duplicates = self.collection.aggregate(pipeline)

        # Iterate over the duplicates
        for duplicate in duplicates:
            # Find one document to keep
            query = {field_to_check: duplicate["_id"]}
            document_to_keep = self.collection.find_one(query)
            
            # Delete all duplicates except one
            query = {field_to_check: duplicate["_id"], "_id": {"$ne": document_to_keep["_id"]}}
            self.collection.delete_many(query)

    def get_all_data(self):

        return self.collection.find({})
    
    def get_unique_estabelecimento(self):
            # Consulta de agregação para encontrar documentos únicos
        pipeline = [
            {
                '$group': {
                    '_id': {
                        'nome': '$estabelecimento.nome',
                        'endereco': '$estabelecimento.endereco',
                        'cnpj': '$estabelecimento.cnpj',
                        'inscricao_estadual': '$estabelecimento.inscricao_estadual'
                    }
                }
            }
        ]

        # Executar a consulta de agregação
        distinct_docs = list(self.collection.aggregate(pipeline))

        return distinct_docs

    def get_unique_compras(self):
            # Consulta de agregação para encontrar documentos únicos
        pipeline = [
            {
                '$group': {
                    '_id': {
                        'cnpj': '$estabelecimento.cnpj',
                        'emissao': '$documento.data_emissao',
                        'chave': '$documento.chave',
                        'valor_pago': '$pagamento.valor_pago'
                    }
                }
            },
            {"$project": {
                "_id": 0,  # Remove o campo _id do resultado final
                "cnpj": "$_id.cnpj",
                "emissao": "$_id.emissao",
                "chave": "$_id.chave",
                "valor_pago": "$_id.valor_pago"
            }}
        ]

        # Executar a consulta de agregação
        distinct_docs = list(self.collection.aggregate(pipeline))

        return distinct_docs
    
    def get_unique_items(self):
            # Consulta de agregação para encontrar documentos únicos
       # Encontrar documentos distintos com base nos campos codigo e descricao dentro do array
        pipeline = [
            {"$unwind": "$itens_nfce"},  # Desnormaliza o array de itens_nfce
            {"$group": {
                "_id": {"codigo": "$itens_nfce.codigo", "descricao": "$itens_nfce.descricao"},
                "quantidade": {"$first": "$itens_nfce.quantidade"},
                "unidade": {"$first": "$itens_nfce.unidade"},
                "valor_unitario": {"$first": "$itens_nfce.valor_unitario"},
                "valor_total": {"$first": "$itens_nfce.valor_total"}
            }},
            {"$project": {
                "_id": 0,  # Remove o campo _id do resultado final
                "codigo": "$_id.codigo",
                "descricao": "$_id.descricao",
                "unidade": 1,
            }}
        ]

        distinct_elements = list(self.collection.aggregate(pipeline))

        return distinct_elements
    
    def get_items_por_compras(self):
            # Consulta de agregação para encontrar documentos únicos
       # Encontrar documentos distintos com base nos campos codigo e descricao dentro do array
        pipeline = [
            {"$unwind": "$itens_nfce"},  # Desnormaliza o array de itens
            {"$project": {
                "_id": 0,
                "chave": "$documento.chave",
                "codigo": "$itens_nfce.codigo",
                "descricao": "$itens_nfce.descricao",
                "quantidade": "$itens_nfce.quantidade",
                "valor_unitario": "$itens_nfce.valor_unitario",
                "valor_total": "$itens_nfce.valor_total"
            }}
        ]

        distinct_elements = list(self.collection.aggregate(pipeline))

        return distinct_elements