
# Usar uma imagem oficial leve do Python
FROM python:3.10-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Instalar dependências do sistema necessárias (incluindo Tesseract OCR e Poppler para PDFs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copiar os requisitos do backend
COPY backend/requirements.txt .

# Instalar as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código do backend para o container
COPY backend/ .

# Expor a porta em que o FastAPI vai correr (o Render injeta a porta dinâmica por variável, mas mantemos a base)
EXPOSE 8000

# Comando para iniciar o servidor Uvicorn (ajustado para a estrutura do backend)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "10000"]