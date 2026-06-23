# ☁️ Almacenamiento en AWS S3 — Guía de Producción para MisterTicket

Esta guía cubre todos los pasos necesarios para migrar el almacenamiento de archivos desde MinIO (local) hacia **AWS S3** en un entorno de producción.

---

## 📋 Estado Previo del Proyecto (Checklist antes de empezar)

Antes de configurar S3, asegúrate de que tu proyecto cumpla con lo siguiente:

- [ ] El backend de Django está desplegado (Heroku, Railway, EC2, etc.)
- [ ] Las dependencias `django-storages` y `boto3` están en `requirements.txt` ✅
- [ ] Las variables de entorno en producción son gestionadas de forma segura (no están en el código fuente)
- [ ] Tu `settings.py` ya lee las variables de entorno para configurar el storage ✅
- [ ] HTTPS está habilitado en el servidor de producción

---

## 🪣 Paso 1: Crear el Bucket S3 en AWS

1. Inicia sesión en [AWS Console](https://console.aws.amazon.com/)
2. Busca el servicio **S3** y haz clic en **Create bucket**
3. Configura el bucket:
   - **Bucket name**: `misterticket-prod` (debe ser único globalmente)
   - **AWS Region**: Elige la más cercana a tus usuarios (ej. `us-east-1` o `sa-east-1` para Sudamérica)
   - **Object Ownership**: Selecciona **ACLs enabled** → **Bucket owner preferred**
4. En la sección **Block Public Access settings**:
   - Desmarca **"Block all public access"**
   - Confirma el aviso que aparece
5. Haz clic en **Create bucket**

---

## 🔓 Paso 2: Configurar Política Pública del Bucket (Bucket Policy)

Para que las imágenes sean accesibles públicamente (sin autenticación):

1. Abre tu bucket → pestaña **Permissions**
2. Ve a **Bucket Policy** → **Edit**
3. Pega la siguiente política (reemplaza `misterticket-prod` con tu nombre de bucket):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::misterticket-prod/*"
    }
  ]
}
```

4. Haz clic en **Save changes**

---

## 👤 Paso 3: Crear Credenciales IAM con Permisos Mínimos

> [!IMPORTANT]
> Nunca uses las credenciales de root de tu cuenta AWS. Crea un usuario IAM con permisos mínimos.

1. Ve al servicio **IAM** → **Users** → **Create user**
2. Nombre de usuario: `misterticket-s3-user`
3. No actives el acceso a la consola de AWS (solo necesita acceso programático)
4. Ve a **Permissions** → **Add permissions** → **Attach policies directly**
5. Haz clic en **Create policy** (en nueva pestaña) con el siguiente JSON:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::misterticket-prod",
        "arn:aws:s3:::misterticket-prod/*"
      ]
    }
  ]
}
```

6. Nombre de la política: `MisterTicketS3Policy`
7. Regresa al usuario IAM y asigna la política `MisterTicketS3Policy`
8. Finaliza la creación del usuario

### Generar Access Keys

1. Abre el usuario `misterticket-s3-user` → pestaña **Security credentials**
2. Haz clic en **Create access key**
3. Selecciona **Application running outside AWS**
4. **⚠️ IMPORTANTE**: Descarga el archivo `.csv` o copia las claves **ahora mismo**. AWS no te las mostrará de nuevo.
   - `Access key ID` → irá en `AWS_ACCESS_KEY_ID`
   - `Secret access key` → irá en `AWS_SECRET_ACCESS_KEY`

---

## ⚙️ Paso 4: Configurar Variables de Entorno en Producción

En tu servidor de producción (o plataforma de deployment), configura las siguientes variables de entorno. **Nunca las pongas en el código fuente ni en `.env` trackeado en git.**

```env
USE_S3=True
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_STORAGE_BUCKET_NAME=misterticket-prod
AWS_S3_REGION_NAME=us-east-1
# Para producción en AWS S3, NO se usa AWS_S3_ENDPOINT_URL (se deja vacío o se omite)
```

### ¿Cómo establecer variables de entorno según el servidor?

**Heroku:**
```bash
heroku config:set USE_S3=True
heroku config:set AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
heroku config:set AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
heroku config:set AWS_STORAGE_BUCKET_NAME=misterticket-prod
heroku config:set AWS_S3_REGION_NAME=us-east-1
```

**Railway:**
Ve a tu proyecto → Variables → Add variable (una por una)

**EC2 / VPS con systemd:**
Edita el archivo de servicio en `/etc/systemd/system/django.service` y agrega las variables en la sección `[Service]`:
```ini
[Service]
Environment="USE_S3=True"
Environment="AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
```

---

## 🔄 Paso 5: Migrar Archivos Existentes a S3 (Opcional)

Si ya tenías archivos en la carpeta local `media/`, puedes subirlos a S3 con el AWS CLI:

```bash
# Instalar AWS CLI si no lo tienes
pip install awscli

# Configurar credenciales
aws configure

# Sincronizar carpeta media local con el bucket S3
aws s3 sync ./media/ s3://misterticket-prod/
```

---

## ✅ Paso 6: Verificar que S3 Funciona Correctamente

### 1. Verificar la configuración de Django

Ejecuta en la consola del servidor:
```bash
python manage.py shell
>>> from django.core.files.storage import default_storage
>>> print(default_storage.__class__)
# Debe mostrar: <class 'storages.backends.s3boto3.S3Boto3Storage'>
```

### 2. Verificar subida de archivo desde Django Shell

```python
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# Crear un archivo de prueba
path = default_storage.save('test/hello.txt', ContentFile(b'Hola S3'))
print(default_storage.url(path))
# Debe retornar una URL tipo: https://misterticket-prod.s3.amazonaws.com/test/hello.txt
```

### 3. Verificar acceso público

Abre la URL del archivo anterior en un navegador. Si puedes ver el contenido, la configuración es correcta.

### 4. Verificar desde la API

Haz un `POST` multipart al endpoint de perfil con una imagen:
```
PUT /api/usuarios/perfil/
Authorization: Bearer <token>
Content-Type: multipart/form-data

foto: <archivo de imagen>
```

La respuesta debería incluir la URL de la imagen en S3, por ejemplo:
```json
{
  "foto": "https://misterticket-prod.s3.amazonaws.com/usuarios/fotos/1/foto_usuario_1.jpg"
}
```

---

## 🔒 Consideraciones de Seguridad en Producción

| Práctica | Descripción |
|---|---|
| **Rotar keys periódicamente** | Genera nuevas credenciales IAM cada 90 días y elimina las antiguas |
| **No trackear .env en git** | Asegúrate que `.env` esté en `.gitignore` |
| **Usar HTTPS** | Las URLs de S3 siempre usan HTTPS por defecto |
| **Habilitar versionado** | En el bucket S3, activa *Versioning* para recuperar archivos eliminados accidentalmente |
| **Configurar CORS en S3** | Si el frontend (Next.js) hace peticiones directas al bucket, agrega reglas CORS en S3 |

### Configuración CORS para S3 (si aplica)

En el bucket → **Permissions** → **Cross-origin resource sharing (CORS)**:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedOrigins": ["https://tu-dominio.com"],
    "ExposeHeaders": []
  }
]
```
