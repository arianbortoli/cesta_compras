FROM python:3.10-slim

# Instalar dependências do sistema (necessário para psycopg2)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY . .

# Expor a porta do Streamlit
EXPOSE 8501

# Comando de inicialização
CMD ["streamlit", "run", "Home.py", "--server.address=0.0.0.0"]

