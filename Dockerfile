# ==========================================
# Dockerfile Optimizado para FastAPI (Backend)
# Proyecto: Analizador Inteligente de Respuestas de Clientes
# ==========================================

# Imagen base liviana de Python
FROM python:3.13-slim

# Evita la creación de archivos .pyc y fuerza el envio inmediato de logs a la consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar primero e instalar dependencias (optimización de capas de cache en Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar todo el código fuente de la aplicación
COPY . .

# Exponer el puerto 8000 donde escuchará Uvicorn
EXPOSE 8000

# Comando de inicio del servidor Uvicorn escuchando en todas las interfaces de red
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
