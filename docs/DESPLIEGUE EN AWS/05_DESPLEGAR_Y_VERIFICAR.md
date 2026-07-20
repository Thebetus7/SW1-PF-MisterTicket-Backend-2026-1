# Paso 5: Subir y Desplegar el Proyecto en AWS

Una vez preparadas las herramientas en el servidor, desplegaremos la aplicación y la base de datos PostgreSQL.

## 4.1 Clonar el proyecto
Clona tu repositorio en la EC2:
```bash
git clone <URL_DEL_REPOSITORIO> misterticket-backend
cd misterticket-backend
```

## 4.2 Subir credenciales de Firebase
Si usas Firebase y `firebase-credentials.json` no está en git, cópialo con `scp` desde tu PC:
```bash
scp -i ~/.ssh/misterticket-backend-key.pem firebase-credentials.json ec2-user@TU_IP_PUBLICA_EC2:/home/ec2-user/misterticket-backend/

```

## 4.3 Levantar contenedores
Levanta los contenedores en segundo plano (background):
```bash
docker-compose up -d --build
```

## 4.4 Configurar base de datos (Migraciones)
Ejecuta las migraciones, carga datos iniciales y recopila estáticos:
```bash
# Correr migraciones de base de datos
docker-compose exec web python manage.py migrate

# Crear superusuario admin
docker-compose exec web python manage.py seed_admin

# (Opcional) Cargar datos de prueba
docker-compose exec web python manage.py seeder_eventos
docker-compose exec web python manage.py seeder_add_artistas

# Recopilar archivos estáticos
docker-compose exec web python manage.py collectstatic --noinput
```

¡Listo! Tu backend está en línea en `http://IP_PUBLICA_EC2/api/`.

---

## ⚠️ Solución de problemas comunes

### `compose build requires buildx 0.17.0 or later`
Ejecuta en la EC2:
```bash
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -L "https://github.com/docker/buildx/releases/download/v0.19.3/buildx-v0.19.3.linux-amd64" -o /usr/local/lib/docker/cli-plugins/docker-buildx
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx
export DOCKER_CLI_PLUGIN_EXTRA_DIRS=/usr/local/lib/docker/cli-plugins
echo 'export DOCKER_CLI_PLUGIN_EXTRA_DIRS=/usr/local/lib/docker/cli-plugins' >> ~/.bashrc
sudo systemctl restart docker
docker-compose up -d --build
```

### Django muestra "Usando MinIO/S3 -> Endpoint: http://localhost:9000" en producción
Si al correr las migraciones o iniciar el backend observas que intenta conectarse a `localhost:9000` en lugar de S3:
* **Causa:** Existe un archivo `.env` residual en el servidor (generalmente subido por error o creado de forma predeterminada) que define la variable `AWS_S3_ENDPOINT_URL=http://localhost:9000`. Django la lee y prioriza sobre la configuración del `docker-compose.yml`.
* **Solución:** Abre el archivo `.env` en el servidor (`nano .env`) y elimina o comenta la línea colocándole un `#` por delante:
  ```env
  # AWS_S3_ENDPOINT_URL=http://localhost:9000
  ```
  Luego reinicia los contenedores:
  ```bash
  docker-compose down && docker-compose up -d
  ```

### S3 Error: "ValueError: Invalid endpoint:" o Error 500 al subir archivos a Amazon
Si la consola de Django muestra un error de `Invalid endpoint: ` vacío al subir archivos:
* **Causa:** En el archivo `core/settings.py`, la variable `AWS_S3_ENDPOINT_URL` lee un texto vacío `''` en lugar de `None` si la variable de entorno está vacía o configurada como `AWS_S3_ENDPOINT_URL=`. Amazon S3 falla al intentar usar el string vacío como URL.
* **Solución:** Asegúrate de que en `core/settings.py` el fallback sea `None`:
  `AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL', None)`

### El contenedor no lee mis cambios en el archivo `.env`
Si editas el `.env` pero el servidor no aplica los cambios (ej. `USE_S3` sigue siendo `False`):
* **Causa 1:** Las variables están escritas directamente (harcodeadas) dentro del archivo `docker-compose.yml` en la sección `environment:`. Lo que esté ahí **sobreescribirá** cualquier valor del `.env`. Además, debe estar presente la instrucción `env_file: - .env` para que el archivo sea leído.
* **Solución 1:** Borra o comenta las variables conflictivas dentro de `docker-compose.yml` y agrégalas a tu `.env`.
* **Causa 2:** Reiniciaste con `docker-compose restart`. Este comando **no lee** cambios en el `.env` ni en el compose.
* **Solución 2:** Usa siempre `docker-compose up -d --force-recreate` para obligarlo a leer la nueva configuración.

### Error 500 en IA Analyzer: "No module named 'pkg_resources'"
Si la subida de canciones falla con error de IA relacionado a `pkg_resources`:
* **Causa:** En versiones recientes de Python, el paquete `setuptools` eliminó el módulo `pkg_resources`. Sin embargo, `imageio-ffmpeg` lo sigue necesitando.
* **Solución:** Limita la versión de setuptools en tu archivo `requirements.txt` a:
  `setuptools<70.0.0`
  Y reconstruye la imagen con `docker-compose up -d --build`.

---

## 🛑 Comandos de Mantenimiento

### Ver Logs:
```bash
docker-compose logs -f web
```

### Detener los Contenedores s:
```bash
docker-compose down
```

### Reiniciar/Levantar de nuevo:
```bash
docker-compose up -d
```

---

> **Siguiente paso:** [06_ACTUALIZAR_PRODUCCION.md](./06_ACTUALIZAR_PRODUCCION.md)  
> **Volver al índice:** [00_RESUMEN_GENERAL.md](./00_RESUMEN_GENERAL.md)
