# 🚀 Despliegue Backend MisterTicket en Render.com (la forma más rápida)

Guía para subir el backend de **MisterTicket** a producción en **Render.com** en menos de **20 minutos**, sin AWS, sin Nginx, sin configurar servidor.

> Si te rendiste con AWS, esta es tu guía. Render se encarga de todo: HTTPS gratis, deploys automáticos desde GitHub y dominio público inmediato.

**Stack que mantenemos:**

- **PostgreSQL:** **Neon** ya configurado en `core/settings.py` (no se toca)
- **Firebase Admin SDK:** archivo `firebase-credentials.json` en la raíz
- **Libélula:** vía variables de entorno en el panel de Render
- **Storage:** local (ver advertencia abajo)

---

## ⚠️ Lo que tienes que saber antes

| Tema | Detalle |
|---|---|
| **Plan gratuito** | El servicio se "duerme" tras 15 min sin tráfico; primera petición tarda ~30s |
| **Filesystem efímero** | Las imágenes subidas a `/media/` **se pierden** en cada redespliegue. Para producción real, activa MinIO/S3 después |
| **Migraciones** | Render no las corre solo — las ejecutas manualmente desde el Shell del dashboard |
| **HTTPS** | Automático (`https://misterticket-backend.onrender.com`) |
| **Tiempo de deploy** | 5–10 min la primera vez, 2–4 min los siguientes |

> Si las imágenes en `/media/` son críticas, salta al final → sección **Storage permanente con Cloudinary o S3**.

---

## 1. Preparar el código (3 cambios mínimos en tu proyecto)

### 1.1 — Agregar `whitenoise` para servir archivos estáticos

Edita **`requirements.txt`** y agrega al final:

```text
whitenoise==6.7.0
```

### 1.2 — Configurar `whitenoise` y `ALLOWED_HOSTS` en `settings.py`

Abre `core/settings.py` y haz **dos cambios pequeños**:

**A) En `MIDDLEWARE`, agrega WhiteNoise justo después de `SecurityMiddleware`:**

```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # <-- nuevo
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... resto igual
]
```

**B) Cambia `ALLOWED_HOSTS` para que acepte cualquier host de Render:**

```python
ALLOWED_HOSTS = ['*']  # Ya estaba así, perfecto para Render
```

**C) Al final del bloque de `STATIC_URL`, agrega:**

```python
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

### 1.3 — Crear el archivo `render.yaml` en la raíz del backend

Este archivo le dice a Render cómo construir y correr tu backend.

📄 **`render.yaml`** (en `MisterTicket/backend/`):

```yaml
services:
  - type: web
    name: misterticket-backend
    runtime: python
    region: oregon
    plan: free
    buildCommand: |
      pip install -r requirements.txt &&
      python manage.py collectstatic --noinput &&
      python manage.py migrate --noinput
    startCommand: gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: "False"
      - key: PYTHON_VERSION
        value: "3.12.4"
      - key: USE_S3
        value: "False"
      - key: LIBELULA_API_KEY
        sync: false
      - key: BACKEND_BASE_URL
        sync: false
```

> `sync: false` significa que esas variables las pondrás tú a mano en el dashboard (más seguro). `generateValue: true` hace que Render cree un `SECRET_KEY` aleatorio.

### 1.4 — Subir todo a GitHub

```bash
cd MisterTicket/backend
git add requirements.txt core/settings.py render.yaml
git commit -m "Preparar despliegue en Render"
git push origin main
```

---

## 2. Crear la cuenta y conectar GitHub

1. Entra a [https://render.com](https://render.com)
2. **Sign up** → elige **GitHub** (más fácil así Render lee tu repo)
3. Autoriza el acceso al repo `MisterTicket` (o solo al folder backend si lo separas)

---

## 3. Desplegar el backend (2 formas)

### Opción A — Con `render.yaml` (Blueprint, recomendado)

1. En el dashboard de Render → botón azul **New +** → **Blueprint**
2. Selecciona el repo `MisterTicket`
3. Render detecta `render.yaml` automáticamente
4. Clic en **Apply**
5. Espera 5–10 min mientras instala y corre el primer build

### Opción B — Manual (sin `render.yaml`)

1. Dashboard → **New +** → **Web Service**
2. Conecta el repo `MisterTicket`
3. Configura:

| Campo | Valor |
|---|---|
| **Name** | `misterticket-backend` |
| **Region** | Oregon (US-West) |
| **Branch** | `main` |
| **Root Directory** | `backend` (si el repo tiene frontend también) |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput` |
| **Start Command** | `gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |
| **Plan** | Free |

4. **Create Web Service**

---

## 4. Configurar las variables de entorno en el dashboard

Después de crear el servicio, ve a la pestaña **Environment** y agrega:

| Variable | Valor |
|---|---|
| `SECRET_KEY` | Ya generado por Render (no tocar) |
| `DEBUG` | `False` |
| `PYTHON_VERSION` | `3.12.4` |
| `USE_S3` | `False` |
| `LIBELULA_API_KEY` | `xOvVur3LHQx7zHknwD2YOp4gS1Rr9U1PZ` (la real de prod) |
| `BACKEND_BASE_URL` | `https://misterticket-backend.onrender.com` (la URL que te da Render) |

Clic en **Save Changes** → Render redespliega automáticamente.

> La base de datos **Neon** ya está hardcodeada en `settings.py`, **no necesitas variables `DB_*`**.

---

## 5. Subir `firebase-credentials.json` a Render

Hay **dos opciones**.

### Opción A — Dejarlo en el repo (más rápido, menos seguro)

Si `firebase-credentials.json` ya está commiteado en GitHub, Render lo trae solo en el build. No haces nada extra.

> Riesgo: cualquiera con acceso al repo ve las credenciales. Acepta esto solo si el repo es **privado**.

### Opción B — Como Secret File en Render (recomendado)

1. Borra `firebase-credentials.json` del repo:
   ```bash
   git rm --cached firebase-credentials.json
   echo "firebase-credentials.json" >> .gitignore
   git commit -m "Sacar credenciales Firebase del repo"
   git push
   ```

2. En Render → tu servicio → pestaña **Environment** → sección **Secret Files**:
   - **Filename**: `firebase-credentials.json`
   - **Contents**: pega el JSON completo del archivo
   - **Save**

3. En `settings.py`, asegúrate de tener algo así (al final):

   ```python
   FIREBASE_CREDENTIALS_PATH = BASE_DIR / 'firebase-credentials.json'
   ```

Render monta el archivo en `/opt/render/project/src/firebase-credentials.json` (la raíz del proyecto) en cada deploy.

---

## 6. Primer despliegue: correr seeders

Una vez que el deploy termine con estado **Live**, abre la pestaña **Shell** (a la derecha del dashboard del servicio):

```bash
python manage.py seed_admin
```

Esto crea el superusuario `admin / admin123` y los usuarios de prueba.

> Para cambiar las credenciales del admin, antes exporta:
> ```bash
> export DJANGO_SUPERUSER_USERNAME=admin
> export DJANGO_SUPERUSER_EMAIL=admin@misterticket.com
> export DJANGO_SUPERUSER_PASSWORD=tu-contraseña-fuerte
> python manage.py seed_admin
> ```

Si quieres datos de demo:

```bash
python manage.py seeder_eventos
python manage.py seeder_add_artistas
```

---

## 7. Probar la API

Tu backend está en línea en:

```
https://misterticket-backend.onrender.com/api/
```

Prueba con curl o navegador:

```bash
curl -I https://misterticket-backend.onrender.com/api/
```

Acceso al admin:

```
https://misterticket-backend.onrender.com/admin/
```

---

## 8. Configurar Libélula con la URL real

Vuelve al dashboard de Render → **Environment** → actualiza:

```
BACKEND_BASE_URL = https://misterticket-backend.onrender.com
```

Render redespliega solo. Los callbacks de Libélula ahora llegarán correctamente.

---

## 🔄 Actualizar el proyecto

Cada `git push` a `main` dispara un **deploy automático** en Render. Solo haz:

```bash
cd MisterTicket/backend
git add .
git commit -m "Lo que cambiaste"
git push origin main
```

En 2–4 min está en producción. Mira el progreso en **Dashboard → Logs**.

### Si cambiaste modelos (necesitas migrar)

Después del deploy, abre **Shell** y ejecuta:

```bash
python manage.py migrate
```

> El `buildCommand` del `render.yaml` ya corre `migrate` en cada deploy, así que normalmente esto **no es necesario**. Solo si quieres forzar.

---

## 🛠️ Troubleshooting

### El deploy falla en `collectstatic`

Falta `STATIC_ROOT` en `settings.py`. Verifica que tengas:

```python
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### `ModuleNotFoundError: whitenoise`

No agregaste `whitenoise==6.7.0` a `requirements.txt`. Agrégalo y haz push.

### El servicio dice **Live** pero la API responde 502 / 503

- El plan free se duerme tras 15 min. Primera petición tarda ~30s en despertar.
- Logs: dashboard → **Logs**. Busca tracebacks de Python.
- Confirma que `gunicorn` está en `requirements.txt`.

### `firebase-admin` no encuentra credenciales

- Opción A: el archivo no está en el repo. Cómmitéalo o usa la Opción B (Secret File).
- Opción B: revisa el nombre exacto en Secret Files (debe ser `firebase-credentials.json`).

### Error de conexión a Neon (`OperationalError`)

- Neon free **pausa la BD** tras 5 min sin actividad. La primera petición la despierta (tarda 1–3s).
- Verifica que `settings.py` tiene `'sslmode': 'require'`.

### Las imágenes subidas desaparecieron

Es el **filesystem efímero** de Render. Cada deploy borra `/media/`. Soluciones:

1. Activar **MinIO/S3** vía las variables `USE_S3`, `AWS_*` (ver siguiente sección)
2. Aceptar que solo es para demo y los datos de prueba se pierden

---

## 🪣 Storage permanente con MinIO o S3 (opcional)

Si necesitas que las fotos de perfil y eventos persistan, **no uses storage local en Render**. Tienes tres opciones rápidas:

### Opción 1 — AWS S3 (más estándar)

1. Crea un bucket en AWS S3 (`misterticket-prod`, región `us-east-2`)
2. Crea un usuario IAM con permisos `s3:*` sobre ese bucket
3. En Render → Environment → agrega:
   ```
   USE_S3=True
   AWS_ACCESS_KEY_ID=AKIA...
   AWS_SECRET_ACCESS_KEY=...
   AWS_STORAGE_BUCKET_NAME=misterticket-prod
   AWS_S3_REGION_NAME=us-east-2
   ```

> Detalles en [`S3_PRODUCCION.md`](./S3_PRODUCCION.md).

### Opción 2 — Cloudinary (gratis hasta 25 GB)

Es más simple que S3, pero requiere agregar `django-cloudinary-storage` y cambiar el storage backend en `settings.py`. Pídelo si lo quieres y te armo el bloque.

### Opción 3 — MinIO en otro servicio

Render no es ideal para MinIO porque también es efímero. Mejor usa S3 directo.

---

## 📊 ¿Quieres una BD también en Render? (en vez de Neon)

Render ofrece PostgreSQL gestionado en plan free (caduca a los 30 días, hay que recrearlo). Si quieres migrar de Neon a Render Postgres:

1. Dashboard → **New +** → **PostgreSQL**
2. **Name**: `misterticket-db`, **Plan**: Free
3. Espera 1–2 min hasta que esté **Available**
4. Copia el **Internal Database URL** (ej. `postgres://user:pass@dpg-xxxx/misterticket_db`)
5. En `settings.py` cambia el bloque `DATABASES` por:

   ```python
   import dj_database_url

   DATABASES = {
       'default': dj_database_url.config(
           default=os.getenv('DATABASE_URL'),
           conn_max_age=600,
           ssl_require=True,
       )
   }
   ```

6. Agrega a `requirements.txt`:
   ```text
   dj-database-url==2.2.0
   ```

7. En Environment del Web Service: `DATABASE_URL = <Internal Database URL>`

**Mi recomendación: quédate con Neon.** No expira y ya está funcionando. No vale la pena migrar solo para "estar todo en Render".

---

## ✅ Checklist final

- [ ] `whitenoise==6.7.0` en `requirements.txt`
- [ ] `WhiteNoiseMiddleware` agregado en `settings.py`
- [ ] `STATIC_ROOT` y `STATICFILES_STORAGE` configurados
- [ ] `render.yaml` en la raíz del backend
- [ ] Push a GitHub hecho
- [ ] Servicio creado en Render como **Blueprint** o **Web Service**
- [ ] Variables `LIBELULA_API_KEY` y `BACKEND_BASE_URL` configuradas
- [ ] `firebase-credentials.json` disponible (repo o Secret File)
- [ ] `seed_admin` ejecutado desde el Shell
- [ ] `https://misterticket-backend.onrender.com/api/` responde
- [ ] `https://misterticket-backend.onrender.com/admin/` te deja entrar con `admin/admin123`

---

## 📌 Comparativa con otras guías

| Tema | `DEPLOY_RENDER.md` (esta) | `DEPLOY_SIMPLE.md` (AWS Docker) | `DOCKER_PRODUCCION.md` |
|---|---|---|---|
| Tiempo de setup | **15–20 min** ⚡ | 30–60 min | 2–4 horas |
| Servidor | Render (PaaS) | EC2 Amazon Linux | EC2 + Nginx + Certbot |
| BD | Neon (sin cambios) | Neon (sin cambios) | Neon o RDS |
| HTTPS | ✅ Automático | ❌ No | ✅ Let's Encrypt |
| Dominio | `*.onrender.com` gratis | IP pública | Tu dominio personalizado |
| Storage permanente | ❌ Requiere S3 aparte | ❌ Requiere MinIO/S3 | ✅ S3 integrado |
| Auto-deploy en `git push` | ✅ Sí | ❌ No (manual SSH) | ❌ No (manual SSH) |
| Dormido por inactividad | ⚠️ Sí (free tier) | ❌ No | ❌ No |
| Costo | $0 (free) o $7/mes | $0 (free tier 12 meses) | $0 inicial, sube con uso |

**Recomendación para MisterTicket:**

- **Hoy (demo/entrega):** Render con esta guía
- **Después (producción real):** migrar a `DOCKER_PRODUCCION.md` cuando tengas tráfico real

---

## 🆘 Resumen ultra-rápido (copiar/pegar)

```bash
# 1. En tu PC
cd MisterTicket/backend
echo "whitenoise==6.7.0" >> requirements.txt
# (editar settings.py: agregar WhiteNoiseMiddleware + STATIC_ROOT)
# (crear render.yaml con el contenido de la sección 1.3)
git add .
git commit -m "Preparar despliegue Render"
git push origin main

# 2. En render.com:
#    Sign up con GitHub → New + → Blueprint → seleccionar repo → Apply

# 3. Esperar 5-10 min

# 4. En Render → Environment, configurar:
#    LIBELULA_API_KEY=xxx
#    BACKEND_BASE_URL=https://tu-app.onrender.com

# 5. En Render → Shell:
python manage.py seed_admin

# 6. Probar: https://tu-app.onrender.com/api/
```

¡Listo, en producción! 🎉
