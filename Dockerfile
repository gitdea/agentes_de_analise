
# Usar uma imagem oficial leve do Python
FROM python:3.10-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Instalar dependências do sistema (Tesseract OCR, Poppler e ferramentas de build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copiar a pasta backend inteira para dentro do container
COPY backend/ /app/backend/

# Instalar todas as dependências Python a partir do diretório correto
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Definir o PYTHONPATH para o Python encontrar a pasta src dentro de backend
ENV PYTHONPATH=/app/backend

# Expor a porta do Render
EXPOSE 10000

# Comando para iniciar o servidor Uvicorn apontando para o caminho correto
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "10000"]