# Paso 7: Configurar Amazon S3 (Opcional pero recomendado)

Por defecto, la configuración rápida guarda las imágenes y archivos dentro del servidor EC2. Si deseas utilizar **Amazon S3** para que el almacenamiento sea escalable y seguro (muy recomendado para producción), sigue estos pasos.

## 7.1 Crear un Bucket en S3

1. Ve a la consola de AWS y busca **S3**.
2. Haz clic en **Crear bucket**.
3. **Nombre del bucket**: `misterticket-archivos` (debe ser un nombre único a nivel mundial).
4. **Región**: Selecciona la misma región donde creaste tu EC2 (ej. `us-east-1` o `sa-east-1`).
5. **Propiedad de objetos**: Selecciona **ACL deshabilitadas** (recomendado).
6. **Bloquear todo el acceso público**: DESMARCA la casilla. Debes permitir acceso público porque los usuarios necesitan poder ver las imágenes de los eventos.
7. Marca la casilla que reconoce que los objetos podrían volverse públicos.
8. Haz clic en **Crear bucket**.

### Agregar política de bucket para acceso de lectura público

Una vez creado, entra a tu bucket > **Permisos** > **Política del bucket** (Editar), y pega lo siguiente (cambiando `misterticket-archivos` por el nombre real de tu bucket):

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
Guarda los cambios.

## 7.2 Crear un Usuario IAM para S3

Para que Django pueda subir archivos, necesitas credenciales:

1. Ve a **IAM** en la consola de AWS.
2. En el menú izquierdo, ve a **Usuarios** y haz clic en **Crear usuario**.
3. Nombre de usuario: `misterticket-s3-user`. Siguiente.
4. Opciones de permisos: **Asociar políticas directamente**.
5. Busca y selecciona la política `AmazonS3FullAccess`. Siguiente > Crear usuario.
6. Una vez creado, haz clic en el usuario `misterticket-s3-user`.
7. Ve a la pestaña **Credenciales de seguridad**.
8. En **Claves de acceso**, haz clic en **Crear clave de acceso**.
9. Selecciona **Aplicación que se ejecuta fuera de AWS**. Siguiente > Crear clave.
10. **IMPORTANTE**: Copia la `Access key` (Clave de acceso) y la `Secret access key` (Clave de acceso secreta). Solo te la mostrarán esta vez.

## 7.3 Actualizar el `docker-compose.yml` en la EC2

Conéctate a tu EC2 por SSH, edita el archivo `docker-compose.yml` (por ejemplo usando `nano docker-compose.yml`) y actualiza el entorno del servicio `web` con las nuevas credenciales. 

Busca la variable `USE_S3=False` y cámbiala a `True`, y agrega las credenciales de tu usuario IAM y tu bucket:

```yaml
    environment:
      # ... otras variables ...
      - USE_S3=True
      - AWS_ACCESS_KEY_ID=TU_ACCESS_KEY
      - AWS_SECRET_ACCESS_KEY=TU_SECRET_KEY
      - AWS_STORAGE_BUCKET_NAME=misterticket-archivos
      - AWS_S3_REGION_NAME=us-east-1  # La región de tu bucket
```

*(No incluyas `AWS_S3_ENDPOINT_URL` para AWS S3 real, solo se usa en MinIO local).*

## 7.4 Reiniciar el Backend

Guarda el archivo y reconstruye/reinicia el contenedor para aplicar los cambios:

```bash
docker-compose down
docker-compose up -d --build
```

¡Listo! Ahora todas las imágenes subidas a los eventos o tickets irán automáticamente a tu bucket de S3.

---

> **Volver al índice:** [00_RESUMEN_GENERAL.md](./00_RESUMEN_GENERAL.md)
