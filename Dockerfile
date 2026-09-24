# Usa uma imagem oficial leve do Python
FROM python:3.12

# Define o diretório de trabalho dentro do container
WORKDIR /app


# Instala o Tesseract, Zbar (para códigos de barras) e dependências gráficas
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    libzbar0 \
    libgl1 \
    libglib2.0-0

# Copia os arquivos de dependência e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da API
COPY . .

# Expõe a porta que o Uvicorn vai rodar
EXPOSE 8000

# Comando para iniciar o FastAPI via Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
