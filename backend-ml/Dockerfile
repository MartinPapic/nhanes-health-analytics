FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar algunas librerías de ML
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y reinstalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código y los modelos
COPY . /app/

# Exponer el puerto
EXPOSE 8000

# Comando para ejecutar FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
