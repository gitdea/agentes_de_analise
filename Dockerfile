
FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema (Tesseract e Poppler)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copiar todo o projeto
COPY . /app

# Instalar todas as dependências do Python (agora com o SQLAlchemy incluído!)
RUN pip install --no-cache-dir -r backend/requirements.txt

# Ir para a pasta backend para correr a aplicação
WORKDIR /app/backend

EXPOSE 10000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "10000"]