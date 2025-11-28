CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS estabelecimentos (
  id SERIAL PRIMARY KEY,
  nome TEXT NOT NULL,
  endereco TEXT,
  cnpj TEXT NOT NULL,
  inscricao_estadual TEXT,
  CONSTRAINT uniq_estab UNIQUE (cnpj)
);

CREATE TABLE IF NOT EXISTS nfe_headers (
  id SERIAL PRIMARY KEY,
  munic TEXT,
  razao_social TEXT,
  emissao DATE,
  numero TEXT,
  tipo_doc TEXT,
  chave_acesso TEXT NOT NULL,
  valor_em_brl NUMERIC(12,2),
  data_registro TIMESTAMP,
  tipo_operacao TEXT,
  situacao_docto TEXT,
  id_estabelecimento INTEGER REFERENCES estabelecimentos(id),
  CONSTRAINT uniq_chave UNIQUE (chave_acesso)
);

CREATE TABLE IF NOT EXISTS itens_nf (
  id SERIAL PRIMARY KEY,
  id_nota INTEGER NOT NULL REFERENCES nfe_headers(id) ON DELETE CASCADE,
  codigo_original TEXT,
  descricao_original TEXT NOT NULL,
  quantidade NUMERIC(12,3),
  unidade TEXT,
  valor_unitario NUMERIC(12,4),
  valor_total NUMERIC(12,2)
);

CREATE TABLE IF NOT EXISTS categorias (
  id SERIAL PRIMARY KEY,
  nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS itens_catalogo (
  id SERIAL PRIMARY KEY,
  nome_padrao TEXT NOT NULL,
  unidade_padrao TEXT,
  id_categoria INTEGER REFERENCES categorias(id)
);

CREATE TABLE IF NOT EXISTS itens_depara (
  id SERIAL PRIMARY KEY,
  descricao_original TEXT NOT NULL,
  id_item_catalogo INTEGER NOT NULL REFERENCES itens_catalogo(id),
  UNIQUE (descricao_original)
);

CREATE INDEX IF NOT EXISTS idx_itensnf_idnota ON itens_nf(id_nota);
CREATE INDEX IF NOT EXISTS idx_itensnf_desc ON itens_nf USING GIN (descricao_original gin_trgm_ops);
