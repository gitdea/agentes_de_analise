
FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema necessárias para OCR e PDFs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copiar os ficheiros de dependências
COPY backend/requirements.txt ./backend/requirements.txt

# Instalar as dependências do Python
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copiar todo o código do projeto para dentro do container
COPY . .

# Definir o diretório de trabalho para dentro do backend onde está o src
WORKDIR /app/backend

# Expor a porta do Render
EXPOSE 10000

# Comando para iniciar o servidor Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "10000"]