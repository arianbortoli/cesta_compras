from db import connect

def run_migrations():
    print("🔄 Verificando e atualizando estrutura do banco de dados...")
    try:
        # Lê o arquivo de schema
        with open("sql/001_schemas.sql", "r") as f:
            schema_sql = f.read()
        
        conn = connect()
        with conn.cursor() as cur:
            # Executa o script SQL inteiro
            cur.execute(schema_sql)
        conn.commit()
        conn.close()
        print("✅ Banco de dados atualizado com sucesso! (Tabelas novas criadas se necessário)")
    except FileNotFoundError:
        print("❌ Erro: Arquivo sql/001_schemas.sql não encontrado.")
    except Exception as e:
        print(f"❌ Erro na migração: {e}")

if __name__ == "__main__":
    run_migrations()

