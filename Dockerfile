# ==============================================================================
# Dockerfile para Thoth Scann
# Arquitectura: Python 3.12 sobre Debian Slim (Ligero, rápido y compatible)
# ==============================================================================

# PASO 1: Imagen Base Oficial
# Usamos 'python:3.12-slim' porque incluye Python optimizado sobre Debian,
# garantizando compatibilidad total con librerías C (NumPy, PyMuPDF, lxml) sin peso extra.
FROM python:3.12-slim

# PASO 2: Variables de Entorno
# - PYTHONDONTWRITEBYTECODE: Evita generar archivos .pyc dentro del contenedor.
# - PYTHONUNBUFFERED: Asegura que los logs de la consola se muestren en tiempo real sin búfer.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true

# PASO 3: Directorio de Trabajo
# Todo lo que se ejecute a partir de aquí ocurrirá dentro de '/app' en el contenedor.
WORKDIR /app

# PASO 4: Dependencias del Sistema Operativo
# Instalamos herramientas necesarias para compilar paquetes C, leer metadatos y procesar multimedia.
# 'rm -rf /var/lib/apt/lists/*' elimina las listas de paquetes para que la imagen sea más liviana.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic1 \
    exiftool \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# PASO 5: Copia e Instalación de Dependencias Python (Estrategia de Caché)
# Copiamos primero 'requirements.txt'. Así, si solo cambias código de tu app,
# Docker no volverá a descargar todas las librerías desde cero.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# PASO 6: Copiar el Código Fuente del Proyecto
# Copia el resto del proyecto respetando las exclusiones definidas en .dockerignore
COPY . .

# PASO 7: Instalar el paquete local MarkItDown
RUN pip install --no-cache-dir -e './markitdown-main/packages/markitdown'

# PASO 8: Crear la carpeta de salida
RUN mkdir -p /app/output

# PASO 9: Puerto Expuesto
# Informa a Docker que el contenedor escuchará en el puerto estándar de Streamlit (8501).
EXPOSE 8501

# PASO 10: Comando de Ejecución
# Inicia la interfaz web en 0.0.0.0 (para que sea accesible desde fuera del contenedor).
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
