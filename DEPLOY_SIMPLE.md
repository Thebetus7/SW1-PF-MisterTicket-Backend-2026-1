# Despliegue Backend MisterTicket en AWS - CON DOCKER (versión simple)

Guía rápida para desplegar el backend de **MisterTicket** (Django + DRF + JWT) en AWS usando **Docker** y **Docker Compose**. Pensada para subir el proyecto a producción **lo antes posible**, sin Nginx, sin HTTPS y sin RDS.

**Stack que mantenemos como ya está en `core/settings.py`:**

- **PostgreSQL:** Neon (no se cambia, credenciales ya hardcodeadas en `settings.py`)
- **Storage:** MinIO local en otro contenedor (opcional) o almacenamiento local
- **Firebase Admin SDK:** archivo `firebase-credentials.json` en la raíz
- **Libélula:** vía variables de entorno
- **JWT, CORS, REST framework:** sin cambios

> Para una guía con Nginx, HTTPS, RDS y seguridad reforzada, ver [`DOCKER_PRODUCCION.md`](./DOCKER_PRODUCCION.md).

---

## 1. Archivos a crear en la raíz del backend

Crea estos dos archivos en `MisterTicket/backend/` (al mismo nivel que `manage.py`).

### 📄 `Dockerfile`

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias del sistema (psycopg2 + Pillow + mutagen)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Código del proyecto (incluye firebase-credentials.json si está presente)
COPY . /app/

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "core.wsgi:application"]
```

### 📄 `docker-compose.yml`

Versión **mínima** (solo Django, usa Neon directamente desde `settings.py`):

```yaml
services:
  web:
    build: .
    container_name: misterticket_backend
    restart: always
    ports:
      - "80:8000"   # Expone el puerto 80 del servidor hacia 8000 del contenedor
    environment:
      - DEBUG=False
      - SECRET_KEY=cambia-esto-por-una-clave-larga-aleatoria
      - LIBELULA_API_KEY=xOvVur3LHQx7zHknwD2YOp4gS1Rr9U1PZ
      - BACKEND_BASE_URL=http://TU_IP_PUBLICA_EC2
      - USE_S3=False
```

> **Importante:** la base de datos **PostgreSQL en Neon** ya está configurada dentro de `core/settings.py` (host `ep-shy-wind-acg84pj4.sa-east-1.aws.neon.tech`). No necesitas variables `DB_*` ni contenedor de BD.

### 📄 `docker-compose.yml` (con MinIO incluido — opcional)

Si quieres tener MinIO corriendo en la misma EC2 para imágenes de eventos y perfiles:

```yaml
services:
  web:
    build: .
    container_name: misterticket_backend
    restart: always
    ports:
      - "80:8000"
    environment:
      - DEBUG=False
      - SECRET_KEY=cambia-esto-por-una-clave-larga-aleatoria
      - LIBELULA_API_KEY=xOvVur3LHQx7zHknwD2YOp4gS1Rr9U1PZ
      - BACKEND_BASE_URL=http://TU_IP_PUBLICA_EC2
      - USE_S3=True
      - AWS_ACCESS_KEY_ID=minioadmin
      - AWS_SECRET_ACCESS_KEY=minioadmin
      - AWS_STORAGE_BUCKET_NAME=misterticket
      - AWS_S3_ENDPOINT_URL=http://minio:9000
    depends_on:
      - minio

  minio:
    image: minio/minio:latest
    container_name: misterticket_minio
    restart: always
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

volumes:
  minio_data:
```

> Para usar MinIO con dominio público necesitarías exponer el puerto 9000 también en el Security Group y crear el bucket `misterticket` con política `download`. Para el primer despliegue rápido, **deja `USE_S3=False`** (las imágenes irán a `/media/` dentro del contenedor).

---

## 2. Crear la Instancia EC2 en AWS

1. **Nombre:** `misterticket-backend`
2. **AMI:** **Amazon Linux 2023 AMI** (capa gratuita)
3. **Tipo de Instancia:** `t3.small` recomendado (2 GiB RAM) — `t2.micro` o `t3.micro` solo si vas justo en presupuesto
4. **Par de claves (SSH):**
   - Crea un nuevo par de claves → `misterticket-key`
   - Tipo: **RSA** · Formato: **`.pem`**
   - Guarda el archivo `.pem` descargado
5. **Security Group:**
   - Permitir **SSH** (puerto `22`) desde tu IP
   - Permitir **HTTP** (puerto `80`) desde `0.0.0.0/0`
   - Si activas MinIO: permitir **TCP `9001`** desde tu IP (consola web de MinIO)
6. **Almacenamiento:** `16 GiB gp3` (más espacio para imágenes de eventos)

Anota la **IP pública** (mejor si asignas una Elastic IP para que no cambie).

---

## 3. Instalar Docker, Buildx y Docker Compose en la EC2

Conéctate por SSH:

```bash
ssh -i misterticket-key.pem ec2-user@TU_IP_PUBLICA_EC2
```

### 3.1 — Instalar Docker y Git

```bash
sudo dnf update -y
sudo dnf install docker git -y

sudo systemctl start docker
sudo systemctl enable docker

sudo usermod -aG docker ec2-user
```

> Cierra SSH con `exit` y vuelve a conectarte para aplicar el grupo `docker`, **o** ejecuta `newgrp docker`.

### 3.2 — Instalar Docker Buildx (obligatorio en Amazon Linux 2023)

```bash
sudo mkdir -p /usr/local/lib/docker/cli-plugins

sudo curl -L "https://github.com/docker/buildx/releases/download/v0.19.3/buildx-v0.19.3.linux-amd64" \
  -o /usr/local/lib/docker/cli-plugins/docker-buildx

sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx

docker buildx version
```

Debe mostrar `v0.19.3` o superior. Si muestra `0.12.1`, fuerza el plugin nuevo:

```bash
echo 'export DOCKER_CLI_PLUGIN_EXTRA_DIRS=/usr/local/lib/docker/cli-plugins' >> ~/.bashrc
source ~/.bashrc
docker buildx version
```

### 3.3 — Instalar Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose

sudo chmod +x /usr/local/bin/docker-compose

docker --version
docker-compose --version
docker buildx version
```

| Comando | Validar |
|---|---|
| `docker --version` | Docker instalado |
| `docker-compose --version` | Compose instalado |
| `docker buildx version` | Versión **≥ 0.17.0** |

---

## 4. Subir y desplegar el proyecto en AWS

### 4.1 — Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO> misterticket-backend
cd misterticket-backend
```

### 4.2 — Subir el archivo de credenciales de Firebase

`firebase-credentials.json` **no debería estar en git**. Cópialo desde tu PC con `scp`:

Desde **tu PC** (otra terminal):

```bash
scp -i misterticket-key.pem firebase-credentials.json \
    ec2-user@TU_IP_PUBLICA_EC2:/home/ec2-user/misterticket-backend/
```

Verifica en el servidor:

```bash
ls -la firebase-credentials.json
```

> Si el archivo está commiteado en el repo, `git clone` ya lo trae y este paso se omite.

### 4.3 — Levantar los contenedores

```bash
docker buildx version          # Confirma >= 0.17.0
docker-compose up -d --build
```

**Salida esperada:**

```text
[+] Building ...
[+] Running 1/1
 ✔ Container misterticket_backend  Started
```

Verifica:

```bash
docker-compose ps
docker-compose logs --tail=50 web
```

### 4.4 — Migraciones y seeders

```bash
# Aplicar migraciones (obligatorio en el primer despliegue)
docker-compose exec web python manage.py migrate

# Crear superusuario admin + usuarios de prueba
docker-compose exec web python manage.py seed_admin

# (Opcional) Datos de demo: departamentos, lugares, eventos
docker-compose exec web python manage.py seeder_eventos

# (Opcional) 15 artistas de prueba
docker-compose exec web python manage.py seeder_add_artistas

# Recopilar archivos estáticos
docker-compose exec web python manage.py collectstatic --noinput
```

| Comando | ¿Cuándo? |
|---|---|
| `migrate` | Siempre en cada despliegue |
| `seed_admin` | **Obligatorio** primera vez (crea `admin/admin123`) |
| `seeder_eventos` | Solo si quieres datos de demo |
| `seeder_add_artistas` | Solo si quieres artistas de demo |
| `collectstatic` | Siempre después de cada despliegue |

> Para producción real, cambia las credenciales por defecto de `seed_admin` exportando antes:
> ```bash
> export DJANGO_SUPERUSER_USERNAME=admin
> export DJANGO_SUPERUSER_EMAIL=admin@misterticket.com
> export DJANGO_SUPERUSER_PASSWORD=tu-contraseña-segura
> docker-compose exec web python manage.py seed_admin
> ```

¡Listo! Tu backend responde en `http://TU_IP_PUBLICA_EC2/api/`.

---

## 5. Variables de entorno de MisterTicket

El proyecto soporta estas variables (en `core/settings.py`). En esta guía las pones directamente en `docker-compose.yml` bajo `environment:`.

| Variable | Para qué sirve | Valor de ejemplo |
|---|---|---|
| `SECRET_KEY` | Clave secreta de Django | Generar con `openssl rand -hex 32` |
| `DEBUG` | Modo debug | `False` en producción |
| `LIBELULA_API_KEY` | API Key de Libélula (pagos) | `xOvVur3LHQ...` |
| `BACKEND_BASE_URL` | URL pública del backend (para callbacks Libélula) | `http://3.148.12.34` |
| `USE_S3` | Activar storage en MinIO/S3 | `False` (local) o `True` (MinIO) |
| `AWS_ACCESS_KEY_ID` | Si `USE_S3=True` | `minioadmin` |
| `AWS_SECRET_ACCESS_KEY` | Si `USE_S3=True` | `minioadmin` |
| `AWS_STORAGE_BUCKET_NAME` | Bucket MinIO | `misterticket` |
| `AWS_S3_ENDPOINT_URL` | Endpoint MinIO interno de Docker | `http://minio:9000` |
| `STRIPE_SECRET_KEY` | Legado, opcional | (vacío) |
| `STRIPE_PUBLISHABLE_KEY` | Legado, opcional | (vacío) |

> La **base de datos Neon** está hardcodeada en `core/settings.py` y **no necesita variables**. Si más adelante quieres mover las credenciales a `.env`, edita `settings.py` para leerlas con `os.getenv(...)`.

---

## ⚠️ Solución de problemas

### `compose build requires buildx 0.17.0 or later`

```bash
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -L "https://github.com/docker/buildx/releases/download/v0.19.3/buildx-v0.19.3.linux-amd64" \
  -o /usr/local/lib/docker/cli-plugins/docker-buildx
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx

echo 'export DOCKER_CLI_PLUGIN_EXTRA_DIRS=/usr/local/lib/docker/cli-plugins' >> ~/.bashrc
source ~/.bashrc

sudo systemctl restart docker
docker-compose up -d --build
```

### `the attribute version is obsolete`

Es solo una **advertencia**. Si tu `docker-compose.yml` tiene `version: '3.8'` arriba, puedes eliminarlo.

### `firebase_admin` no encuentra credenciales

Confirma que `firebase-credentials.json` está dentro del contenedor:

```bash
docker-compose exec web ls -la firebase-credentials.json
```

Si no aparece, vuelve al paso **4.2** (subir el archivo con `scp`) y reconstruye:

```bash
docker-compose up -d --build
```

### Libélula no llega al backend (callback)

- `BACKEND_BASE_URL` debe ser la **IP pública** o dominio real, no `localhost`
- El puerto **80** debe estar abierto en el Security Group desde `0.0.0.0/0`
- Verifica:
  ```bash
  curl -I http://TU_IP_PUBLICA_EC2/api/
  ```

### Error de conexión a Neon

- Neon **exige SSL** (`settings.py` ya tiene `sslmode: require`)
- Verifica que la EC2 puede salir a internet (regla outbound default abierta)
- Mira los logs:
  ```bash
  docker-compose logs --tail=50 web | grep -i "operational\|connect"
  ```

---

## 🛑 Comandos de mantenimiento

```bash
# Ver logs en vivo
docker-compose logs -f web

# Reiniciar solo el backend
docker-compose restart web

# Detener todo
docker-compose down

# Levantar de nuevo
docker-compose up -d

# Limpiar imágenes viejas
docker system prune -f
```

---

## 🔄 Actualizar el proyecto en producción

### A) En tu PC

```bash
cd MisterTicket/backend
git add .
git commit -m "Descripción del cambio"
git push origin main
```

### B) En la EC2

```bash
# 1. Conectarte
ssh -i misterticket-key.pem ec2-user@TU_IP_PUBLICA_EC2

# 2. Entrar al proyecto
cd /home/ec2-user/misterticket-backend

# 3. Traer el código nuevo
git pull origin main

# 4. Reconstruir y reiniciar
docker buildx version              # Confirma >= 0.17.0
docker-compose up -d --build

# 5. Migraciones + estáticos (siempre)
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput

# 6. Verificar
docker-compose ps
docker-compose logs --tail=30 web
```

### Resumen rápido (copiar/pegar en el servidor)

```bash
cd /home/ec2-user/misterticket-backend
git pull origin main
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
docker-compose ps
docker-compose logs --tail=30 web
```

> El volumen `minio_data` y la base Neon **conservan los datos** entre despliegues. `--build` solo recompila la imagen de Django.

---

## ✅ Checklist final

- [ ] EC2 Amazon Linux 2023 corriendo en `us-east-2`
- [ ] Security Group: 22 (SSH), 80 (HTTP), 9001 opcional (MinIO consola)
- [ ] Docker + Buildx ≥ 0.17.0 + Docker Compose instalados
- [ ] `Dockerfile` y `docker-compose.yml` en la raíz del backend
- [ ] `firebase-credentials.json` presente en `/home/ec2-user/misterticket-backend/`
- [ ] `SECRET_KEY` cambiado por uno aleatorio
- [ ] `BACKEND_BASE_URL` apunta a la IP pública real
- [ ] `LIBELULA_API_KEY` es la real de producción
- [ ] `docker-compose up -d --build` levanta el contenedor `misterticket_backend`
- [ ] `seed_admin` ejecutado al menos una vez
- [ ] `http://IP_PUBLICA/api/` responde

---

## 📌 Diferencias con `DOCKER_PRODUCCION.md`

| Tema | `DEPLOY_SIMPLE.md` (esta guía) | `DOCKER_PRODUCCION.md` |
|---|---|---|
| Base de datos | **Neon** ya hardcodeada en `settings.py` | RDS o Neon vía `.env.production` |
| Nginx + HTTPS | ❌ No (puerto 80 directo a Gunicorn) | ✅ Sí (Nginx + Certbot) |
| Dominio + DNS | Opcional (usa IP pública) | Configurado (`api.misterticket.com`) |
| Storage | MinIO en contenedor o local | AWS S3 con IAM Role |
| Variables sensibles | En `docker-compose.yml` | En `.env.production` con `chmod 600` |
| Tiempo de setup | **15–30 min** | 1–2 horas |
| Para qué sirve | Subir rápido a producción / demo | Producción robusta a largo plazo |

Cuando el proyecto madure, migra de `DEPLOY_SIMPLE.md` a `DOCKER_PRODUCCION.md`.
