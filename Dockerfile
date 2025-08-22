FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

# Criar usuário que pode acessar docker
RUN useradd -m -u 1000 botuser
RUN chown -R botuser:botuser /app

USER botuser

CMD ["python", "bot.py"]