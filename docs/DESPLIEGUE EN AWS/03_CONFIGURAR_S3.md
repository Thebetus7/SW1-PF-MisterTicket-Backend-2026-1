# Paso 3: Configurar AWS S3 para Almacenamiento y Reproducción de Canciones

En desarrollo local, el backend utiliza **MinIO** mediante un contenedor Docker para simular el almacenamiento en la nube. Para producción en AWS, migraremos el almacenamiento a un bucket de **Amazon S3** con los permisos adecuados para que las imágenes de los eventos se visualicen y las canciones subidas por los artistas puedan reproducirse en streaming en el navegador sin problemas.

---

## 3.1 — Crear un Bucket en S3 con Acceso de Lectura Público

Los archivos de audio (canciones) y de imágenes de eventos de MisterTicket deben ser accesibles públicamente desde el navegador del usuario para que el reproductor de audio y el sitio web puedan cargarlos directamente.

Sigue estos pasos en la consola de AWS:

1. Busca y selecciona **S3** en la barra de búsqueda de la consola de AWS.
2. Haz clic en **Create bucket** (Crear bucket).
3. Configura los parámetros generales:
   * **Bucket name:** `misterticket-archivos` (debe ser un nombre globalmente único en todo AWS).
   * **AWS Region:** Selecciona la misma región donde desplegarás tu servidor EC2 (ej. `us-east-1` o `sa-east-1`).
4. **Object Ownership:** Selecciona **ACLs disabled (recommended)**.
5. **Block Public Access settings for this bucket:**
   * **DESMARCA** la opción **Block *all* public access** (Bloquear todo el acceso público).
   * Deja desmarcadas todas las casillas inferiores.
   * **IMPORTANTE:** Marca la casilla de verificación inferior que dice *"I acknowledge that the current settings might result in this bucket and the objects within it becoming public"* (Reconozco que la configuración actual puede hacer que este bucket y los objetos dentro de él sean públicos). Esto es necesario para que el frontend pueda leer las canciones e imágenes.
6. **Bucket Versioning:** Selecciona **Disable** (o **Enable** si deseas mantener historial de archivos modificados).
7. **Encryption:** Deja activado **Server-side encryption with Amazon S3-managed keys (SSE-S3)**.
8. Haz clic en **Create bucket** (Crear bucket).

---

## 3.2 — Agregar la Política del Bucket (Bucket Policy)

Una vez creado el bucket, debes conceder permisos de lectura pública a cualquier objeto dentro de él:

1. Entra a tu bucket recién creado (`misterticket-archivos`) en la consola de S3.
2. Haz clic en la pestaña **Permissions** (Permisos).
3. Baja hasta la sección **Bucket policy** (Política de bucket) y haz clic en **Edit** (Editar).
4. Pega la siguiente política en formato JSON (reemplaza `misterticket-archivos` por el nombre real de tu bucket si es distinto):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::misterticket-archivos/*"
        }
    ]
}
```

5. Haz clic en **Save changes** (Guardar cambios).

---

## 3.3 — Configurar CORS para Streaming de Canciones (Audio)

Cuando el navegador (o la aplicación móvil) intente reproducir canciones directamente desde S3 mediante el reproductor HTML5, realizará peticiones de tipo **CORS** y solicitudes de rango HTTP (`Range Requests`) para permitir adelantar o retroceder la canción. Si no configuras CORS correctamente, el navegador bloqueará la reproducción o impedirá adelantar la pista de audio.

1. Permanece en la pestaña **Permissions** (Permisos) de tu bucket.
2. Baja hasta el final a la sección **Cross-origin resource sharing (CORS)** y haz clic en **Edit** (Editar).
3. Pega la siguiente configuración de CORS, la cual expone las cabeceras de rango (`Range`) necesarias para la reproducción multimedia:

```json
[
    {
        "AllowedHeaders": [
            "*"
        ],
        "AllowedMethods": [
            "GET",
            "PUT",
            "POST",
            "DELETE",
            "HEAD"
        ],
        "AllowedOrigins": [
            "*"
        ],
        "ExposeHeaders": [
            "ETag",
            "Content-Type",
            "Content-Length",
            "Accept-Ranges",
            "Content-Range"
        ],
        "MaxAgeSeconds": 3000
    }
]
```

4. Haz clic en **Save changes** (Guardar cambios).

---

## 3.4 — Crear el Usuario IAM y Adjuntar la Política de Escritura

Para que el backend (Django) pueda conectarse a S3 para subir archivos cuando un artista agregue una canción o un administrador cree un evento, necesita credenciales seguras. Crearemos un usuario IAM dedicado con permisos limitados a nuestro bucket.

### A) Crear la Política de Permisos S3
1. Busca **IAM** en la consola de AWS.
2. En el menú lateral izquierdo, haz clic en **Policies** (Políticas) y luego en **Create policy** (Crear política).
3. Selecciona la pestaña **JSON** y borra el contenido por defecto.
4. Pega la siguiente política (reemplaza `misterticket-archivos` por el nombre de tu bucket):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "S3BackendStorageAccess",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            "Resource": [
                "arn:aws:s3:::misterticket-archivos",
                "arn:aws:s3:::misterticket-archivos/*"
            ]
        }
    ]
}
```

5. Haz clic en **Next** (Siguiente).
6. Nombra la política como: `misterticket-s3-policy`.
7. Haz clic en **Create policy** (Crear política).

### B) Crear el Usuario IAM
1. En el menú lateral de **IAM**, ve a **Users** (Usuarios) y presiona **Create user** (Crear usuario).
2. Asigna el nombre de usuario: `misterticket-s3-user`.
3. Deja **desmarcada** la casilla *Provide user access to the AWS Management Console*. Presiona **Next**.
4. En **Permissions options** (Opciones de permisos), selecciona **Attach policies directly** (Asociar políticas directamente).
5. Busca `misterticket-s3-policy` en el listado, selecciónala y haz clic en **Next**.
6. Revisa y haz clic en **Create user** (Crear usuario).

### C) Generar las Claves de Acceso (Access Keys)
1. En la lista de usuarios, haz clic en `misterticket-s3-user`.
2. Ve a la pestaña **Security credentials** (Credenciales de seguridad).
3. En la sección **Access keys**, haz clic en **Create access key** (Crear clave de acceso).
4. Elige el caso de uso **Application running outside AWS** (Aplicación que se ejecuta fuera de AWS). Haz clic en **Next**.
5. (Opcional) Asigna una etiqueta descriptiva (ej. `Django backend storage`).
6. Haz clic en **Create access key**.
7. **ADVERTENCIA CRÍTICA:** Descarga el archivo `.csv` con tus credenciales y guárdalo de manera segura.
   * **AWS_ACCESS_KEY_ID:** ID de la clave de acceso.
   * **AWS_SECRET_ACCESS_KEY:** Clave secreta (solo se mostrará esta vez).

---

## 3.5 — Configuración en el Servidor EC2 (Producción)

Dado que el backend de Django ya está preparado en su archivo `settings.py` para leer del entorno, **no necesitas cambiar el código Python**. Solo debes inyectar las credenciales correspondientes a nivel de variables de entorno en el servidor.

1. Conéctate a tu instancia EC2 por SSH (ver detalles en el flujo de despliegue).
2. Abre y edita el archivo `docker-compose.yml` en el servidor:
   ```bash
   nano docker-compose.yml
   ```
3. En la sección de variables de entorno (`environment`) de tu servicio `web` (Django), configura las variables correspondientes a S3:

```yaml
    environment:
      # ... otras variables ...
      - USE_S3=True
      - AWS_ACCESS_KEY_ID=TU_ACCESS_KEY_ID_DESCARGADO
      - AWS_SECRET_ACCESS_KEY=TU_SECRET_ACCESS_KEY_DESCARGADO
      - AWS_STORAGE_BUCKET_NAME=misterticket-archivos
      - AWS_S3_REGION_NAME=us-east-1  # Reemplaza por tu región si es distinta
```

> [!WARNING]
> **Cuidado con el archivo `.env` residual en el servidor:**
> Dado que Django lee el archivo `.env` al iniciar (mediante `load_dotenv()`), si existe un archivo `.env` en el servidor que contiene la línea `AWS_S3_ENDPOINT_URL=http://localhost:9000` (o similar), Django la priorizará e intentará conectarse a MinIO local en lugar de a AWS S3 real.
> **Solución:** Edita el archivo `.env` en tu servidor (`nano .env`) y elimina o comenta esa línea (poniendo un `#` al inicio: `#AWS_S3_ENDPOINT_URL=...`). Lo ideal en producción es que elimines el archivo `.env` por completo y manejes todo a través del entorno del `docker-compose.yml`.

4. Guarda los cambios en `nano` presionando `Ctrl + O`, presiona `Enter` para confirmar, y luego sal con `Ctrl + X`.

5. Reinicia los contenedores de Docker para aplicar los cambios:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

---

> **Siguiente paso:** [04_INSTALAR_HERRAMIENTAS.md](./04_INSTALAR_HERRAMIENTAS.md)  
> **Volver al índice:** [00_RESUMEN_GENERAL.md](./00_RESUMEN_GENERAL.md)
