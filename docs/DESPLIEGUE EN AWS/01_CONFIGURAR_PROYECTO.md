# Paso 1: Archivos de Configuración Requeridos en tu Proyecto

Para habilitar Docker en el backend de **MisterTicket**, debes asegurarte de tener los siguientes dos archivos en la raíz de tu carpeta `MisterTicket/backend/`:

### 📄 `Dockerfile`
Este archivo en la raíz del backend define cómo se construye la imagen de la aplicación Django:
```dockerfile
FROM python:3.12-slim

# Evitar que Python escriba archivos .pyc y forzar salida de logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema (psycopg2 + Pillow + mutagen + ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias del proyecto
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copiar el código del proyecto (incluye firebase-credentials.json si está presente)
COPY . /app/

# Exponer el puerto de Django/Gunicorn
EXPOSE 8000

# Comando para correr en producción
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "core.wsgi:application"]
```

### 📄 `docker-compose.yml`
Este archivo orquesta la aplicación web y la base de datos PostgreSQL de forma local en el contenedor:
```yaml
services:
  db:
    image: postgres:15-alpine
    container_name: misterticket_db
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_DB=misterticket_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=123456789
    ports:
      - "5432:5432"

  web:
    build: .
    container_name: misterticket_backend
    restart: always
    command: gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 core.wsgi:application
    volumes:
      - .:/app
    ports:
      - "80:8000"  # Expone el puerto 80 del servidor hacia el 8000 del contenedor
    environment:
      - DEBUG=False
      - SECRET_KEY=cambia-esto-por-una-clave-larga-aleatoria
      - LIBELULA_API_KEY=xOvVur3LHQx7zHknwD2YOp4gS1Rr9U1PZ
      - BACKEND_BASE_URL=http://TU_IP_PUBLICA_EC2
      - USE_S3=False
      - DB_NAME=misterticket_db
      - DB_USER=postgres
      - DB_PASSWORD=123456789
      - DB_HOST=db  # Apunta al nombre del servicio de la BD
      - DB_PORT=5432
    depends_on:
      - db

volumes:
  postgres_data:
```

> [!NOTE]
> **Sobre MinIO vs AWS S3:** 
> Por defecto, esta plantilla utiliza almacenamiento local. Si vas a habilitar AWS S3 real para producción en tu servidor (siguiendo el Paso 3), asegúrate de que no exista la variable `AWS_S3_ENDPOINT_URL` en tu entorno ni en un archivo `.env` residual en el servidor, ya que Django prioriza el archivo `.env` y esto haría que intente conectarse al puerto local `9000` (MinIO local).

---

> **Siguiente paso:** [02_CREAR_INSTANCIA_EC2.md](./02_CREAR_INSTANCIA_EC2.md)  
> **Volver al índice:** [00_RESUMEN_GENERAL.md](./00_RESUMEN_GENERAL.md)
