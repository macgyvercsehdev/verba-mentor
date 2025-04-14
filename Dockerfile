FROM python:3.11-slim

# Definir variáveis de ambiente para otimizar Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    python3-dev \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements.txt e instalar dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar certificado de banco de dados se existir
COPY db_ca.crt* ./

# Copiar código fonte
COPY src/ /app/src/

# Criar arquivos __init__.py para resolver problemas de importação
RUN find /app/src -type d -exec touch {}/__init__.py \;

# Criar diretório para dados persistentes
RUN mkdir -p /app/data

# Criar script de entrypoint
RUN echo '#!/bin/sh\necho "Iniciando Bot de Tutoria de Inglês..."\nexec python -m src.main' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Definir comando para executar o bot
CMD ["/app/entrypoint.sh"] 