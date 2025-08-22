FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY bot.py .
COPY .env .

# Criar usuário que pode acessar docker
# Usar o GID correto do grupo docker (1001 no seu caso)
RUN groupadd -g 1001 docker || true
RUN useradd -m -u 1000 -G docker botuser

# Dar permissões adequadas
RUN chown -R botuser:botuser /app

# Trocar para o usuário
USER botuser

CMD ["python", "bot.py"]