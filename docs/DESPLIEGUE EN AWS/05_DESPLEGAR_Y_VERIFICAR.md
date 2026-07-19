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
