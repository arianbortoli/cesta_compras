import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

def connect():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "n8n"),
        user=os.getenv("DB_USER", "n8n"),
        password=os.getenv("DB_PASSWORD", "senha"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
    )

# ---------- helpers ----------
def _to_float(s):
    if s is None: return None
    if isinstance(s, (int, float)): return float(s)
    s = str(s).strip()

    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


# ---------- leitura ----------
def fetch_table(table_name):
    conn = connect()
    try:
        df = pd.read_sql(f'SELECT * FROM "{table_name}"', conn)
        return df
    finally:
        conn.close()



# ---------- headers ----------
def fetch_existing_chave_acesso():
    try:
        conn = connect()
        with conn.cursor() as cur:
            cur.execute('SELECT chave_acesso FROM nfe_headers')
            rows = cur.fetchall()
        return {row[0] for row in rows} if rows else set()
    except Exception:
        return set()
    finally:
        try: conn.close()
        except: pass



def insert_new_nfes(df):
    conn = connect()
    try:
        df["chave_acesso"] = df["chave_acesso"].str.replace(" ", "")
        existing_keys = fetch_existing_chave_acesso()
        df_new = df[~df["chave_acesso"].isin(existing_keys)]
        if df_new.empty:
            return 0

        rows = [
            (
                row.munic, row.razao_social,
                pd.to_datetime(row.emissao).date() if pd.notna(row.emissao) else None,
                row.numero, row.tipo_doc,
                row.chave_acesso, _to_float(row.valor_em_brl),
                pd.to_datetime(row.data_registro) if pd.notna(row.data_registro) else None,
                row.tipo_operacao, row.situacao_docto
            )
            for row in df_new.itertuples(index=False)
        ]

        with conn.cursor() as cur:
            execute_values(cur, """
                INSERT INTO nfe_headers (
                    munic, razao_social, emissao, numero, tipo_doc,
                    chave_acesso, valor_em_brl, data_registro,
                    tipo_operacao, situacao_docto
                ) VALUES %s
                ON CONFLICT (chave_acesso) DO NOTHING
            """, rows)
        conn.commit()
        return len(rows)
    finally:
        conn.close()

def chave_ja_processada(chave):
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM nfe_headers WHERE chave_acesso = %s", (chave,))
            return cur.fetchone() is not None
    finally:
        conn.close()

def get_nfe_id_by_chave(chave):
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM nfe_headers WHERE chave_acesso = %s", (chave,))
            r = cur.fetchone()
            return r[0] if r else None
    finally:
        conn.close()

def fetch_existing_item_notas():
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT id_nota FROM itens_nf")
            rows = cur.fetchall()
        return {row[0] for row in rows} if rows else set()
    finally:
        conn.close()

# ---------- estabelecimentos ----------
def get_or_create_estabelecimento(estabelecimento_dict):
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM estabelecimentos WHERE cnpj = %s", (estabelecimento_dict["cnpj"],))
            r = cur.fetchone()
            if r:
                return r[0]
            cur.execute("""
                INSERT INTO estabelecimentos (nome, endereco, cnpj, inscricao_estadual)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (cnpj) DO NOTHING
                RETURNING id
            """, (
                estabelecimento_dict["nome"],
                estabelecimento_dict.get("endereco", ""),
                estabelecimento_dict["cnpj"],
                estabelecimento_dict.get("inscricao_estadual","")
            ))
            got = cur.fetchone()
            if got:
                conn.commit()
                return got[0]
            # se caiu em DO NOTHING, buscar de novo
            cur.execute("SELECT id FROM estabelecimentos WHERE cnpj = %s", (estabelecimento_dict["cnpj"],))
            return cur.fetchone()[0]
    finally:
        conn.close()

# ---------- itens ----------
def inserir_itens_nf(id_nfe, lista_itens):
    conn = connect()
    try:
        rows = []
        for item in lista_itens:
            rows.append((
                id_nfe,
                item.get("codigo", ""),
                item.get("descricao", ""),
                _to_float(item.get("quantidade")),
                item.get("unidade", ""),
                _to_float(item.get("valor_unitario")),
                _to_float(item.get("valor_total")),
            ))
        with conn.cursor() as cur:
            execute_values(cur, """
                INSERT INTO itens_nf (
                    id_nota, codigo_original, descricao_original, quantidade,
                    unidade, valor_unitario, valor_total
                ) VALUES %s
            """, rows)
        conn.commit()
    finally:
        conn.close()

# ---------- padronização ----------
def get_unmapped_items():

    """Retorna descrições originais que ainda não têm vínculo no de-para."""
    conn = connect()
    try:
        with conn.cursor() as cur:
            # Itens que estão nas notas mas não na tabela itens_depara
            cur.execute("""
                SELECT DISTINCT i.descricao_original
                FROM itens_nf i
                LEFT JOIN itens_depara d ON i.descricao_original = d.descricao_original
                WHERE d.id IS NULL
                ORDER BY i.descricao_original
            """)
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

def get_categories():
    conn = connect()
    try:
        df = pd.read_sql("SELECT * FROM categorias ORDER BY nome", conn)
        return df
    finally:
        conn.close()

def create_category(nome):
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO categorias (nome) VALUES (%s) ON CONFLICT (nome) DO NOTHING", (nome,))
        conn.commit()
    finally:
        conn.close()

def get_catalog_items():
    conn = connect()
    try:
        query = """
            SELECT c.id, c.nome_padrao, c.unidade_padrao, cat.nome as categoria
            FROM itens_catalogo c
            LEFT JOIN categorias cat ON c.id_categoria = cat.id
            ORDER BY c.nome_padrao
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()

def create_catalog_item(nome, unidade, id_categoria):
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO itens_catalogo (nome_padrao, unidade_padrao, id_categoria)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (nome, unidade, id_categoria))
            conn.commit()
            return cur.fetchone()[0]
    finally:
        conn.close()

def link_items(original_descriptions, id_catalogo):
    """Vincula uma lista de descrições originais a um item do catálogo."""
    conn = connect()
    try:
        data = [(desc, id_catalogo) for desc in original_descriptions]
        with conn.cursor() as cur:
            execute_values(cur, """
                INSERT INTO itens_depara (descricao_original, id_item_catalogo)
                VALUES %s
                ON CONFLICT (descricao_original) DO NOTHING
            """, data)
        conn.commit()
    finally:
        conn.close()

# ---------- analises ----------
def get_general_analytics():
    conn = connect()
    try:
        # Esta query calcula médias (7/30 dias), min/max e busca o nome do local mais barato
        query = """
            WITH stats AS (
                SELECT
                    cat.id,
                    cat.nome_padrao,
                    c.nome as categoria,
                    cat.unidade_padrao,
                    AVG(i.valor_unitario) FILTER (WHERE h.emissao >= CURRENT_DATE - INTERVAL '7 days') as media_7d,
                    AVG(i.valor_unitario) FILTER (WHERE h.emissao >= CURRENT_DATE - INTERVAL '30 days') as media_30d,
                    MIN(i.valor_unitario) as preco_min,
                    MAX(i.valor_unitario) as preco_max
                FROM itens_catalogo cat
                LEFT JOIN categorias c ON cat.id_categoria = c.id
                JOIN itens_depara d ON cat.id = d.id_item_catalogo
                JOIN itens_nf i ON d.descricao_original = i.descricao_original
                JOIN nfe_headers h ON i.id_nota = h.id
                GROUP BY cat.id, cat.nome_padrao, c.nome, cat.unidade_padrao
            ),
            best_place AS (
                SELECT DISTINCT ON (cat.id)
                    cat.id,
                    e.nome as local_mais_barato,
                    h.emissao as data_melhor_preco
                FROM itens_catalogo cat
                JOIN itens_depara d ON cat.id = d.id_item_catalogo
                JOIN itens_nf i ON d.descricao_original = i.descricao_original
                JOIN nfe_headers h ON i.id_nota = h.id
                JOIN estabelecimentos e ON h.id_estabelecimento = e.id
                ORDER BY cat.id, i.valor_unitario ASC, h.emissao DESC
            )
            SELECT 
                s.nome_padrao,
                s.categoria,
                s.unidade_padrao,
                ROUND(s.media_7d, 2) as media_7d,
                ROUND(s.media_30d, 2) as media_30d,
                ROUND(s.preco_min, 2) as preco_min,
                ROUND(s.preco_max, 2) as preco_max,
                bp.local_mais_barato,
                bp.data_melhor_preco
            FROM stats s
            LEFT JOIN best_place bp ON s.id = bp.id
            ORDER BY s.nome_padrao
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()

def get_price_history(product_name):
    conn = connect()
    try:
        query = """
            SELECT 
                h.emissao, 
                i.valor_unitario, 
                e.nome as estabelecimento
            FROM itens_catalogo cat
            JOIN itens_depara d ON cat.id = d.id_item_catalogo
            JOIN itens_nf i ON d.descricao_original = i.descricao_original
            JOIN nfe_headers h ON i.id_nota = h.id
            JOIN estabelecimentos e ON h.id_estabelecimento = e.id
            WHERE cat.nome_padrao = %s
            ORDER BY h.emissao
        """
        return pd.read_sql(query, conn, params=(product_name,))
    finally:
        conn.close()

# ---------- cesta inteligente ----------
def calculate_basket_best_place(product_ids):
    if not product_ids:
        return pd.DataFrame()
        
    conn = connect()
    try:
        # Formatar tuple para SQL
        ids_tuple = tuple(product_ids)
        
        query = """
            WITH latest_prices AS (
                SELECT DISTINCT ON (e.id, cat.id)
                    e.id as estab_id,
                    e.nome as estab_nome,
                    cat.id as prod_id,
                    cat.nome_padrao as prod_nome,
                    i.valor_unitario
                FROM estabelecimentos e
                JOIN nfe_headers h ON e.id = h.id_estabelecimento
                JOIN itens_nf i ON h.id = i.id_nota
                JOIN itens_depara d ON i.descricao_original = d.descricao_original
                JOIN itens_catalogo cat ON d.id_item_catalogo = cat.id
                WHERE cat.id IN %s
                ORDER BY e.id, cat.id, h.emissao DESC
            )
            SELECT
                estab_nome,
                COUNT(prod_id) as itens_encontrados,
                SUM(valor_unitario) as total_estimado,
                array_to_string(array_agg(prod_nome || ' (R$ ' || round(valor_unitario, 2) || ')'), ', ') as detalhes
            FROM latest_prices
            GROUP BY estab_id, estab_nome
            ORDER BY itens_encontrados DESC, total_estimado ASC
        """
        # Psycopg2 precisa de adaptação para tupla de 1 elemento
        if len(ids_tuple) == 1:
            # Hack para evitar erro de sintaxe com tupla de 1 elemento no python vs sql
            # Mas execute_values ou params handles it usually.
            # Vamos passar direto, o cursor.execute lida bem com tuplas se for %s
            pass
            
        return pd.read_sql(query, conn, params=(ids_tuple,))
    finally:
        conn.close()


