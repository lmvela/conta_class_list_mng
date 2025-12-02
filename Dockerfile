# Usa una imagen ligera de Python
FROM python:3.11-slim

# Evita que Python genere archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
# Incluye git, rsync, bash y certificados para HTTPS
RUN apt-get update && \
    apt-get install -y git rsync bash iputils-ping netcat-openbsd build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir gunicorn
RUN pip install --no-cache-dir -r requirements.txt

# Copiar toda la app
COPY app/ /app/

# Puerto interno donde correrá Flask vía Gunicorn
EXPOSE 9005

# Comando de producción: Gunicorn
#
# -w 4  → 4 workers (ajusta según CPU)
# -b 0.0.0.0:9005 → escucha en el puerto 9005
# "app:app" → archivo app.py con variable "app"
#
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:9005", "app:app"]
