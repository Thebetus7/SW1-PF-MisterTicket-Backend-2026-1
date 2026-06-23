# 📦 MinIO Local con Docker — MisterTicket

Guía para gestionar el contenedor de **MinIO** en tu entorno de desarrollo local.

## 📋 Requisitos Previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y en ejecución.
- Archivo `.env` en `backend/` con las variables `MINIO_ROOT_USER` y `MINIO_ROOT_PASSWORD`.

---

## 🚀 Encender MinIO

```powershell
# Desde la carpeta backend/
docker compose -f docker-compose-minio.yml up -d
```

Verifica que esté corriendo:
```powershell
docker compose -f docker-compose-minio.yml ps
```

---

## 🌐 Acceder a la Consola Web

Una vez encendido, abre tu navegador en:

- **Consola de Administración**: http://localhost:9001
- **Usuario**: el valor de `MINIO_ROOT_USER` en tu `.env` (default: `minioadmin`)
- **Contraseña**: el valor de `MINIO_ROOT_PASSWORD` en tu `.env` (default: `minioadmin`)

---

## 🪣 Crear y Configurar el Bucket

Solo debes hacer esto la **primera vez** que levantes MinIO.

### 1. Crear el Bucket
Puedes crearlo ingresando a http://localhost:9001 -> **Buckets** -> **Create Bucket** -> Nombre: `misterticket`.

### 2. Hacer el Bucket Público (Access Policy: download/public)
> [!IMPORTANT]
> En versiones recientes de MinIO Community Edition, la consola web no incluye el switch directo para configurar políticas públicas o requiere configuraciones complejas. La forma 100% fiable de hacerlo sin instalar nada en tu PC es ejecutar la CLI `mc` integrada **dentro del propio contenedor de Docker**:

Ejecuta el siguiente comando en tu terminal (PowerShell o Git Bash) para configurar la política de descarga pública en tu bucket:

```powershell
# 1. Crear el alias local dentro del contenedor
docker exec misterticket_minio mc alias set myminio http://localhost:9000 minioadmin minioadmin

# 2. Configurar la política de descarga (download) para el bucket misterticket
docker exec misterticket_minio mc anonymous set download myminio/misterticket
```

Para verificar que la política se aplicó correctamente, puedes ejecutar:
```powershell
docker exec misterticket_minio mc anonymous list myminio/misterticket
```
Debería mostrar `download` para el bucket.

---

## ⚙️ Configurar Django para usar MinIO

En tu archivo `.env` (backend), asegúrate de tener:

```env
# ─── MinIO / S3 Storage (local) ────────────────────────
USE_S3=True
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_STORAGE_BUCKET_NAME=misterticket
AWS_S3_ENDPOINT_URL=http://localhost:9000
```

> [!IMPORTANT]
> **Reinicio de Django**: Después de cambiar `USE_S3=True` en el archivo `.env`, **DEBES reiniciar por completo** el servidor de Django (`python manage.py runserver`) para que cargue la nueva configuración del storage. Si no lo reinicias, Django continuará guardando las fotos en la ruta local `/media/` en lugar de subirlas al bucket de MinIO.

---

## 🛠️ Resolución de Problemas Comunes (Troubleshooting)

### 1. Error de permisos al guardar archivos (403 Forbidden / AccessDenied)
Si Django te da un error de permisos o el almacenamiento local sigue cargando de forma "fallback" tras configurar MinIO, verifica que en `backend/core/settings.py` tengas configurado:
```python
AWS_DEFAULT_ACL = None
```
**Razón**: MinIO no soporta ACLs de AWS por defecto (como `'public-read'`). Intentar enviar un ACL provoca que la firma falle y MinIO rechace la subida de archivos.

### 2. La imagen se guarda en MinIO pero no se visualiza en la App Móvil (Flutter)
Si estás ejecutando la aplicación de Flutter en un **Emulador de Android**, este no resolverá `localhost:9000` (el puerto apunta al propio emulador). 
- **Solución automática**: El código en `ProfileProvider` detecta si la plataforma es móvil y reescribe de forma dinámica las referencias de `localhost:9000` y `127.0.0.1:9000` a `10.0.2.2:9000` (la IP reservada para acceder al host local desde Android), garantizando que las imágenes de perfil locales se carguen perfectamente.
- **En dispositivos reales**: Si estás probando la app en tu teléfono celular físico mediante Tunnelmole (`npx tunnelmole 8000`), recuerda que Tunnelmole solo expone el puerto `8000` del backend. El puerto `9000` de MinIO no está expuesto a internet. Para pruebas en teléfonos físicos, te recomendamos usar almacenamiento local (`USE_S3=False`) o configurar un túnel adicional para el puerto `9000` si es estrictamente necesario.

---

## 🛑 Apagar MinIO (sin borrar datos)

```powershell
docker compose -f docker-compose-minio.yml stop
```

Para volver a encenderlo sin perder los datos:
```powershell
docker compose -f docker-compose-minio.yml start
```

---

## 🗑️ Eliminar MinIO (apagar Y borrar todos los datos)

> [!WARNING]
> Este comando elimina el contenedor **y todos los archivos almacenados**. No hay vuelta atrás.

```powershell
# Detener y eliminar contenedor + red
docker compose -f docker-compose-minio.yml down

# Eliminar también los volúmenes (datos del disco)
docker compose -f docker-compose-minio.yml down --volumes
```
