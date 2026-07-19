# Paso 8: Eliminar todo rastro de Docker (Contenedores, Volúmenes e Imágenes)

Si necesitas reiniciar tu servidor a un estado limpio o liberar espacio en disco eliminando por completo los contenedores, volúmenes e imágenes de Docker creados en el proyecto, sigue las siguientes instrucciones.

> [!CAUTION]
> Eliminar los volúmenes de Docker borrará la base de datos local y todos sus datos guardados (usuarios, eventos, tickets, etc.). Asegúrate de no requerir esa información antes de continuar.

---

## Opción 1: Limpieza del proyecto actual (Recomendado)

Si estás en el directorio del proyecto donde se encuentra el archivo `docker-compose.yml`, ejecuta el siguiente comando:

```bash
docker compose down -v --rmi all
```

### ¿Qué hace este comando?
* **`down`**: Detiene y elimina los contenedores y redes creados por este proyecto.
* **`-v` / `--volumes`**: Elimina los volúmenes de datos persistentes definidos en el `docker-compose.yml` (por ejemplo, el volumen de la base de datos PostgreSQL `postgres_data`).
* **`--rmi all`**: Elimina todas las imágenes de Docker creadas para este proyecto (tanto la del contenedor `web` de Django como las de dependencias asociadas).

---

## Opción 2: Limpieza total de todo el sistema Docker (Borrado absoluto)

Si deseas hacer una limpieza general en el servidor para borrar cualquier contenedor, imagen o volumen residual (incluso de otros proyectos o contenedores huérfanos), ejecuta estos comandos:

### 1. Detener todos los contenedores activos
```bash
docker stop $(docker ps -aq)
```

### 2. Eliminar todos los contenedores
```bash
docker rm $(docker ps -aq)
```

### 3. Eliminar todos los volúmenes de datos
```bash
docker volume rm $(docker volume ls -q)
```

### 4. Eliminar todas las imágenes de Docker
```bash
docker rmi -f $(docker images -aq)
```

### 5. Purgar el sistema de manera automática (Alternativa rápida)
Puedes resumir todo lo anterior ejecutando una purga completa que borra contenedores apagados, redes en desuso, caché de construcción y volúmenes colgantes:

```bash
docker system prune -a --volumes -f
```

---

> **Volver al índice:** [00_RESUMEN_GENERAL.md](./00_RESUMEN_GENERAL.md)
