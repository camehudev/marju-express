# Usa uma imagem oficial leve do Python
FROM python:3.12

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Exemplo para Debian/Ubuntu no Dockerfile
RUN apt-get update && apt-get install -y \
    libzbar0 \
    tesseract-ocr

# Copia os arquivos de dependência e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da API
COPY . .

# Expõe a porta que o Uvicorn vai rodar
EXPOSE 8000

# Comando para iniciar o FastAPI via Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
