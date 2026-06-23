# Despliegue Backend (Django + PostgreSQL) en AWS - CON DOCKER

Esta guía describe cómo empaquetar y desplegar el backend de **GestorLab** en AWS usando **Docker** y **Docker Compose**. Este enfoque aislará la aplicación y la base de datos PostgreSQL en contenedores independientes de forma limpia.

---

## 1. Archivos de Configuración Requeridos en tu Proyecto

Para habilitar Docker en tu proyecto backend, debes crear los siguientes dos archivos en la raíz de tu carpeta `gestor-lab-backend/`:

### 📄 `Dockerfile`
Crea este archivo en la raíz del backend:
```dockerfile
FROM python:3.11-slim

# Evitar que Python escriba archivos .pyc y forzar salida de logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias para compilar psycopg2 (controlador PostgreSQL)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias del proyecto
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copiar el código del proyecto
COPY . /app/

# Exponer el puerto de Django/Gunicorn
EXPOSE 8000

# Comando para correr en producción
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]
```

### 📄 `docker-compose.yml`
Crea este archivo en la raíz del backend para orquestar la app y la base de datos PostgreSQL:
```yaml
services:
  db:
    image: postgres:15-alpine
    container_name: gestorlab_db
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_DB=SW2_GestorLab_1_26
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=123456789
    ports:
      - "5432:5432"

  web:
    build: .
    container_name: gestorlab_backend
    restart: always
    command: gunicorn --bind 0.0.0.0:8000 core.wsgi:application
    volumes:
      - .:/app
    ports:
      - "80:8000"  # Expone el puerto 80 del servidor hacia el 8000 del contenedor
    environment:
      - DEBUG=False
      - SECRET_KEY=TU_LLAVE_SECRETA_SUPER_SEGURA_PROD
      - DB_NAME=SW2_GestorLab_1_26
      - DB_USER=postgres
      - DB_PASSWORD=123456789
      - DB_HOST=db  # Apunta al nombre del servicio de la BD
      - DB_PORT=5432
    depends_on:
      - db

volumes:
  postgres_data:
```

---

## 2. Crear la Instancia EC2 en AWS

1. **Nombre:** `gestorlab-backend-docker`
2. **AMI:** **Amazon Linux 2023 AMI** (capa gratuita).
3. **Tipo de Instancia:** `t2.micro` o `t3.micro`.
4. **Par de claves (inicio de sesión - SSH):**
   * Haz clic en **"Crear un nuevo par de claves"** (si no tienes una).
   * Llámalo `gestorlab-backend-key`.
   * Tipo de clave: **RSA**. Formato de archivo: **`.pem`**.
   * Presiona **Crear**. Tu navegador descargará automáticamente el archivo `gestorlab-backend-key.pem`. **Guárdalo en un lugar seguro**, ya que lo usarás para conectarte por SSH.
5. **Configuraciones de red (Security Group):**
   - Permitir **SSH** (puerto `22`) desde cualquier lugar (`0.0.0.0/0`).
   - Permitir **HTTP** (puerto `80`) desde cualquier lugar (`0.0.0.0/0`) (ya que Docker Compose mapeará el puerto 80 del servidor directamente a la app).
5. **Almacenamiento:** `8 GiB gp3`.

---

## 3. Instalar Docker, Buildx y Docker Compose en la EC2

Conéctate por SSH a la EC2 y ejecuta los pasos en orden.

> **¿Por qué Buildx es obligatorio?**  
> En **Amazon Linux 2023**, el paquete `docker` trae Buildx **0.12.1**, pero Docker Compose moderno exige **Buildx 0.17.0 o superior** para compilar imágenes (`docker-compose up --build`).  
> El paquete `docker-buildx-plugin` **no existe** en los repositorios de Amazon Linux 2023 (`No match for argument: docker-buildx-plugin`). Por eso hay que instalar Buildx **manualmente** en todos los servidores nuevos.

### 3.1 — Instalar Docker y Git

```bash
# Actualizar el sistema
sudo dnf update -y

# Instalar Docker y Git (NO incluye Buildx compatible con Compose)
sudo dnf install docker git -y

# Iniciar Docker y habilitarlo al arranque del servidor
sudo systemctl start docker
sudo systemctl enable docker

# Permitir que ec2-user use Docker sin sudo
sudo usermod -aG docker ec2-user
```

> [!IMPORTANT]
> Para aplicar el grupo `docker` en tu sesión actual:
> 1. Cierra SSH con `exit` y vuelve a conectarte, **o**
> 2. Ejecuta: `newgrp docker`

### 3.2 — Instalar Docker Buildx (obligatorio en Amazon Linux 2023)

```bash
# Crear carpeta de plugins de Docker CLI
sudo mkdir -p /usr/local/lib/docker/cli-plugins

# Descargar Buildx 0.19.3 (compatible con Docker Compose actual)
sudo curl -L "https://github.com/docker/buildx/releases/download/v0.19.3/buildx-v0.19.3.linux-amd64" \
  -o /usr/local/lib/docker/cli-plugins/docker-buildx

sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx
```

**Verificar que la versión es correcta** (debe ser **0.17.0 o superior**):

```bash
docker buildx version
```

**Salida esperada:**

```text
github.com/docker/buildx v0.19.3 ...
```

**Si aún muestra `0.12.1`**, Docker está usando el Buildx viejo del paquete `docker`. Fuerza el plugin nuevo:

```bash
export DOCKER_CLI_PLUGIN_EXTRA_DIRS=/usr/local/lib/docker/cli-plugins
docker buildx version
```

Para que persista en futuras sesiones SSH, agrégalo al perfil del usuario:

```bash
echo 'export DOCKER_CLI_PLUGIN_EXTRA_DIRS=/usr/local/lib/docker/cli-plugins' >> ~/.bashrc
source ~/.bashrc
docker buildx version
```

> **No continúes** al paso 4 si `docker buildx version` sigue mostrando menos de `0.17.0`. Sin esto, `docker-compose up -d --build` fallará con:  
> `compose build requires buildx 0.17.0 or later`

### 3.3 — Instalar Docker Compose

```bash
# Descargar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose

sudo chmod +x /usr/local/bin/docker-compose

# Verificar instalación completa
docker --version
docker-compose --version
docker buildx version
```

**Checklist antes de desplegar** (los tres deben responder sin error):

| Comando | Qué validar |
|---|---|
| `docker --version` | Docker instalado |
| `docker-compose --version` | Compose instalado |
| `docker buildx version` | Versión **≥ 0.17.0** (ideal: `v0.19.3`) |

---

## 4. Subir y Desplegar el Proyecto en AWS

1. Clona tu repositorio en la EC2:
   ```bash
   git clone <URL_DEL_REPOSITORIO> gestor-lab-backend
   cd gestor-lab-backend
   ```
2. **Confirma que Buildx está listo** (solo la primera vez o si ves el error de buildx):
   ```bash
   docker buildx version
   ```
   Debe mostrar `v0.17.0` o superior. Si no, vuelve a la [sección 3.2](#32--instalar-docker-buildx-obligatorio-en-amazon-linux-2023).

3. Levanta los contenedores en segundo plano (background):
   ```bash
   docker-compose up -d --build
   ```
4. Ejecuta las migraciones, carga los usuarios semilla y recopila estáticos dentro del contenedor de Django:
   ```bash
   # Correr migraciones de base de datos
   docker-compose exec web python manage.py migrate
   
   # Crear usuarios y roles iniciales (admin, operador, auxiliares)
   docker-compose exec web python manage.py seed_users
   
   # Recopilar archivos estáticos
   docker-compose exec web python manage.py collectstatic --noinput
   ```

   > **Nota:** El comando `seed_users` (`usuarios/autenticacion/management/commands/seed_users.py`) es **obligatorio** en el primer despliegue. Crea los grupos `admin`, `operador` y `auxiliar`, y los usuarios iniciales del sistema (`admin`, `operador_test`, `auxBeto`, `auxJuan`). Si ya existen, actualiza sus credenciales sin duplicarlos.

¡Listo! Tu backend está en línea en `http://IP_PUBLICA_EC2/api`.

---

## ⚠️ Solución de problemas

### `compose build requires buildx 0.17.0 or later`

**Qué significa:** Docker Compose intentó **construir la imagen** del backend (`build: .` en `docker-compose.yml`), pero Buildx no cumple el mínimo requerido (**0.17.0**). En Amazon Linux 2023 es muy común tener **0.12.1** por defecto.

**Causa habitual en Amazon Linux 2023:**
- `sudo dnf install docker-buildx-plugin` → falla con `No match for argument`
- `docker buildx version` → muestra `0.12.1`

**Solución** (ejecuta en la EC2):

```bash
# 1. Instalar Buildx actualizado manualmente
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -L "https://github.com/docker/buildx/releases/download/v0.19.3/buildx-v0.19.3.linux-amd64" \
  -o /usr/local/lib/docker/cli-plugins/docker-buildx
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx

# 2. Verificar versión (debe ser >= 0.17.0)
docker buildx version

# 3. Si sigue en 0.12.1, forzar el plugin nuevo
export DOCKER_CLI_PLUGIN_EXTRA_DIRS=/usr/local/lib/docker/cli-plugins
echo 'export DOCKER_CLI_PLUGIN_EXTRA_DIRS=/usr/local/lib/docker/cli-plugins' >> ~/.bashrc
docker buildx version

# 4. Reiniciar Docker y reintentar despliegue
sudo systemctl restart docker
cd ~/gestor-lab-backend
docker-compose up -d --build
```

**Plan B** (si Compose sigue fallando al build):

```bash
cd ~/gestor-lab-backend
docker build -t gestor-lab-backend-web .
docker-compose up -d
docker-compose ps
```

### `the attribute version is obsolete`

**Qué significa:** Es solo una **advertencia**, no un error. Las versiones nuevas de Docker Compose ya no usan la línea `version: '3.8'` al inicio del archivo. Puedes ignorarla o eliminar esa línea de `docker-compose.yml`.

---

## 🛑 Comandos de Mantenimiento

### Ver Logs:
```bash
docker-compose logs -f web
```

### Detener los Contenedores:
```bash
docker-compose down
```

### Reiniciar/Levantar de nuevo:
```bash
docker-compose up -d
```

---

## 🔄 Actualizar el Proyecto en Producción (Desplegar Nuevos Cambios)

Cuando modificas código en tu PC y quieres que esos cambios se reflejen en AWS, el flujo es:

1. **Subes el código a GitHub** desde tu computadora.
2. **Entras al servidor AWS por SSH** y descargas ese código nuevo.
3. **Reconstruyes los contenedores Docker** para que usen el código actualizado.
4. **Ejecutas migraciones** si cambiaste la base de datos.

> **Importante:** Los pasos de la sección **A** los haces en tu PC. Los de la sección **B** los haces **dentro del servidor AWS**, después de conectarte por SSH.

---

### A) En tu PC local (antes de tocar el servidor)

Abre una terminal en la carpeta del proyecto backend en tu computadora:

```bash
cd gestor-lab-backend
```

Guarda tus cambios y súbelos a GitHub:

```bash
git add .
git commit -m "Descripción breve de lo que cambiaste"
git push origin main
```

**Qué hace cada comando:**
- `git add .` → marca todos los archivos modificados para subirlos.
- `git commit` → crea un "paquete" con esos cambios y un mensaje.
- `git push` → envía ese paquete a GitHub.

**Espera a que termine el push.** Solo cuando GitHub ya tenga el código nuevo, pasas al servidor.

---

### B) En el servidor AWS (paso a paso)

#### B.1 — Conectarte al servidor por SSH

Desde **tu PC**, abre una terminal y conéctate a la EC2.

**En Windows (PowerShell):** ve a la carpeta donde guardaste el archivo `.pem`:

```powershell
cd C:\ruta\donde\guardaste\la\clave
ssh -i gestorlab-backend-key.pem ec2-user@TU_IP_PUBLICA_EC2
```

**En Linux/Mac:**

```bash
ssh -i gestorlab-backend-key.pem ec2-user@TU_IP_PUBLICA_EC2
```

Reemplaza `TU_IP_PUBLICA_EC2` por la IP que ves en la consola de AWS (ejemplo: `54.123.45.67`).

**Si la conexión es correcta**, verás un prompt como este:

```text
[ec2-user@ip-172-31-41-220 ~]$
```

Eso significa que **ya estás dentro del servidor**. Todo lo que escribas a partir de aquí se ejecuta en AWS, no en tu PC.

---

#### B.2 — Ir a la carpeta del proyecto en el servidor

El repositorio se clonó en el primer despliegue. Entra a esa carpeta:

```bash
cd /home/ec2-user/gestor-lab-backend
```

**Verifica que estás en el lugar correcto:**

```bash
pwd
ls
```

**Qué deberías ver:**
- `pwd` debe mostrar: `/home/ec2-user/gestor-lab-backend`
- `ls` debe listar archivos como `docker-compose.yml`, `Dockerfile`, `manage.py`, `core/`, etc.

Si `ls` dice "No such file or directory", el proyecto no está ahí. Revisa si lo clonaste con otro nombre o en otra ruta.

---

#### B.3 — Descargar el código nuevo desde GitHub

Con la carpeta correcta abierta, trae los cambios que subiste desde tu PC:

```bash
git pull origin main
```

**Qué hace:** compara el código del servidor con GitHub y actualiza los archivos locales del servidor.

**Salida esperada si todo va bien:**

```text
Updating abc1234..def5678
Fast-forward
 usuarios/views.py | 10 +++++-----
 1 file changed, 5 insertions(+), 5 deletions(-)
```

**Si Git dice** `Already up to date`, el servidor ya tenía la última versión (quizá el `git push` desde tu PC no se completó).

**Si Git pide usuario/contraseña** y falla, el repo puede ser privado. En ese caso configura acceso con token o SSH en el servidor (fuera del alcance de esta guía básica).

---

#### B.4 — Reconstruir y reiniciar los contenedores

Sigue en la misma carpeta (`/home/ec2-user/gestor-lab-backend`).

**Antes de construir**, confirma que Buildx es compatible (evita el error `compose build requires buildx 0.17.0 or later`):

```bash
docker buildx version
```

Debe mostrar **0.17.0 o superior**. Si muestra `0.12.1`, aplica la [sección 3.2](#32--instalar-docker-buildx-obligatorio-en-amazon-linux-2023) o la [solución de problemas](#compose-build-requires-buildx-0170-or-later) antes de continuar.

Luego reconstruye y levanta los contenedores:

```bash
docker-compose up -d --build
```

**Qué hace cada parte:**
- `up` → levanta (o reinicia) los contenedores.
- `-d` → los deja corriendo en segundo plano (no bloquea la terminal).
- `--build` → **vuelve a construir la imagen** del backend con el código que acabas de bajar.

**Salida esperada si todo va bien:**

```text
[+] Building ...
[+] Running 2/2
 ✔ Container gestorlab_db       Running
 ✔ Container gestorlab_backend  Started
```

**Verifica que los contenedores están activos:**

```bash
docker-compose ps
```

Deberías ver `gestorlab_db` y `gestorlab_backend` con estado `Up`.

> **Nota:** Este comando **no borra la base de datos**. Los datos de PostgreSQL viven en un volumen Docker (`postgres_data`) y se conservan entre actualizaciones.

---

#### B.5 — Aplicar migraciones y archivos estáticos (dentro del contenedor)

Estos comandos se ejecutan **dentro del contenedor `web`**, no directamente en el servidor. Docker los envía al contenedor de Django por ti.

**Siempre ejecuta `migrate`** después de actualizar (aunque no hayas tocado modelos, no hace daño):

```bash
docker-compose exec web python manage.py migrate
```

**Qué hace:** aplica cambios pendientes en la estructura de la base de datos (nuevas tablas, columnas, etc.).

**Recopila archivos estáticos** (CSS, JS admin, etc.):

```bash
docker-compose exec web python manage.py collectstatic --noinput
```

**Solo si agregaste o modificaste usuarios semilla**, ejecuta también:

```bash
docker-compose exec web python manage.py seed_users
```

| Comando | ¿Cuándo ejecutarlo? |
|---|---|
| `migrate` | **Siempre** después de cada actualización |
| `collectstatic` | **Siempre** después de cada actualización |
| `seed_users` | Solo si cambiaste `seed_users.py` o es un despliegue inicial |

---

#### B.6 — Comprobar que la actualización funcionó

**1. Revisa los logs del backend** (busca errores):

```bash
docker-compose logs --tail=50 web
```

Si ves tracebacks de Python o errores de conexión a la BD, algo falló en el paso anterior.

**2. Prueba la API desde tu navegador o Postman:**

```text
http://TU_IP_PUBLICA_EC2/api/
```

**3. (Opcional) Verifica que responde desde el propio servidor:**

```bash
curl -I http://localhost/api/
```

Deberías recibir una respuesta HTTP (por ejemplo `200 OK` o `404` si no hay ruta raíz, pero **no** un error de conexión).

**4. Salir del servidor cuando termines:**

```bash
exit
```

Eso cierra la sesión SSH y vuelves a la terminal de tu PC.

---

#### B.7 — Limpiar espacio en disco (opcional)

Cada `--build` deja imágenes Docker viejas ocupando espacio. En una EC2 pequeña (`t2.micro`) conviene limpiar de vez en cuando:

```bash
docker system prune -f
```

**Qué hace:** elimina imágenes y capas que ya no usa ningún contenedor. **No borra** el volumen de PostgreSQL ni los contenedores en ejecución.

---

### Resumen rápido (solo servidor AWS)

Copia y pega esto en orden **después de conectarte por SSH** y **después de haber hecho `git push` desde tu PC**:

```bash
cd /home/ec2-user/gestor-lab-backend
git pull origin main
docker buildx version
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
docker-compose ps
docker-compose logs --tail=30 web
```

> Si `docker buildx version` muestra menos de `0.17.0`, **no ejecutes** `docker-compose up -d --build` todavía. Corrige Buildx primero (sección 3.2).
