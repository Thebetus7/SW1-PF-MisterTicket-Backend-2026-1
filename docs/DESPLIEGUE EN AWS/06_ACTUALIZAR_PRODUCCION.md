# Paso 6: Actualizar el Proyecto en Producción

Cuando modificas código en tu PC y quieres que esos cambios se reflejen en AWS, el flujo es el siguiente:

### A) En tu PC local (antes de tocar el servidor)

Abre una terminal en la carpeta del proyecto backend en tu computadora:

```bash
cd MisterTicket/backend
```

Guarda tus cambios y súbelos a GitHub:

```bash
git add .
git commit -m "Descripción breve de lo que cambiaste"
git push origin main
```

### B) En el servidor AWS

**1. Conéctate por SSH:**
```bash
ssh -i misterticket-key.pem ec2-user@TU_IP_PUBLICA_EC2
```

**2. Ve a la carpeta del proyecto:**
```bash
cd /home/ec2-user/misterticket-backend
```

**3. Descarga el código nuevo desde GitHub:**
```bash
git pull origin main
```

**4. Reconstruye y reinicia los contenedores:**
```bash
docker-compose up -d --build
```

**5. Aplica migraciones y archivos estáticos:**
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

**6. Comprueba que la actualización funcionó revisando los logs:**
```bash
docker-compose logs --tail=50 web
```
*(Si observas la línea `[STORAGE] >> Usando MinIO/S3 -> ... | Endpoint: http://localhost:9000` y quieres usar AWS S3 real en la nube, recuerda borrar o comentar la variable `AWS_S3_ENDPOINT_URL` de tu archivo `.env` local en el servidor).*

**7. Verifica que los contenedores estén activos y corriendo correctamente:**
```bash
docker-compose ps
```

---

### Resumen rápido (solo servidor AWS)

Copia y pega esto en orden después de conectarte por SSH:

```bash
cd /home/ec2-user/misterticket-backend
git pull origin main
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
docker-compose ps
docker-compose logs --tail=30 web
```

---

### C) Limpieza y Re-despliegue Absoluto (Desde cero)

Si necesitas restaurar todo el backend a un estado limpio y vacío (por ejemplo, para borrar todos los usuarios de prueba, eventos creados y re-inicializar el esquema de datos):

> [!CAUTION]
> Esto eliminará de forma permanente la base de datos de Docker y todos sus registros (usuarios, entradas vendidas, eventos, etc.). Asegúrate de no requerir esa información.

1. **Detener y eliminar los contenedores junto con sus volúmenes:**
   ```bash
   docker-compose down -v
   ```
   *(El flag `-v` destruye por completo el volumen `postgres_data` de Postgres).*

2. **(Opcional) Limpiar el almacenamiento en AWS S3:**
   * Si usas S3 y quieres borrar también los archivos de audio e imágenes subidos, ingresa a la consola web de AWS S3, selecciona los objetos dentro de tu bucket `misterticket-archivos` y haz clic en **Eliminar** (o **Vaciar bucket**).

3. **Reconstruir y levantar el backend limpio:**
   ```bash
   docker-compose up -d --build
   ```

4. **Ejecutar migraciones y semilla de datos básicos iniciales:**
   ```bash
   # Aplicar la estructura de la base de datos vacía
   docker-compose exec web python manage.py migrate

   # Crear usuario administrador inicial
   docker-compose exec web python manage.py seed_admin

   # (Opcional) Cargar semilla de artistas y eventos de prueba
   docker-compose exec web python manage.py seeder_eventos
   docker-compose exec web python manage.py seeder_add_artistas

   # Colectar estáticos
   docker-compose exec web python manage.py collectstatic --noinput
   ```

---

> **Siguiente paso:** [07_APAGAR_SERVICIOS.md](./07_APAGAR_SERVICIOS.md)  
> **Volver al índice:** [00_RESUMEN_GENERAL.md](./00_RESUMEN_GENERAL.md)
