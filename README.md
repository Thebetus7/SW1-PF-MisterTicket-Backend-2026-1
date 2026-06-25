# MisterTicket Backend - Guía de Base de Datos

> **Esquema y tablas del proyecto:** consulta [`ESTRUCTURA_BD.md`](./ESTRUCTURA_BD.md) (modelos, relaciones, roles y flujo de datos).

Este documento explica cómo gestionar la base de datos en Django, especialmente si vienes de un entorno como **Laravel** y buscas comandos como `php artisan migrate:fresh`.

## 🔄 El equivalente a `migrate:fresh` en Django

En Laravel, `migrate:fresh` elimina todas las tablas y vuelve a ejecutar las migraciones. En Django, el proceso es un poco más explícito.

### Opción 1: Limpiar solo los datos (Flush)

Si solo quieres vaciar las tablas pero mantener la estructura intacta (sin borrar atributos o campos nuevos):

```bash
python manage.py flush
```

_Esto eliminará todos los registros de la base de datos pero conservará las tablas._

---

### Opción 2: Reset Total (El "Fresh" Real)

Si has hecho cambios estructurales (añadir/quitar atributos en `models.py`) y quieres "limpiar" todo para empezar de cero porque las migraciones se han vuelto confusas:

1. **Eliminar los archivos de migración:**
   Debes borrar los archivos numerados dentro de las carpetas `migrations` de cada app, **PERO NO** borres el archivo `__init__.py`.
   - `apps/usuarios/migrations/0001_...` (Borrar este)
   - `apps/usuarios/migrations/__init__.py` (**NO** borrar este)

2. **Limpiar la Base de Datos (PostgreSQL):**
   Dado que usas PostgreSQL (según tu `.env`), puedes resetear la base de datos desde la consola de Postgres o una herramienta como pgAdmin:

   ```sql
   DROP DATABASE mister_ticket;
   CREATE DATABASE mister_ticket;
   ```

3. **Generar y aplicar nuevas migraciones (Reset total):**
   Si deseas empezar desde cero absoluto, borra los archivos de la carpeta `migrations` de cada app (excepto `__init__.py`) y ejecuta:

   ```bash
   # Borrar archivos de migración (Windows PowerShell)
   Get-ChildItem -Path "apps\*\migrations\*.py" -Exclude "__init__.py" | Remove-Item -Force

   # Re-generar y aplicar
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Ejecutar Seeders (Cargar datos iniciales):**
   Después de correr las migraciones, debes ejecutar los seeders en el siguiente orden para cargar la base de datos con información inicial de prueba:

   ```bash
   # 1. Crear el superusuario y roles
   python manage.py seed_admin

   # 2. Agregar 15 artistas de ejemplo
   python manage.py seeder_add_artistas

   # 3. Crear lugares, departamentos y 2 eventos
   python manage.py seeder_eventos
   ```

---

## 🛠️ Flujo Normal de Cambios (Sin borrar todo)

A diferencia de Laravel donde sueles crear una nueva migración para añadir un campo, en Django el flujo es:

1. **Modifica tu modelo:** Añade el atributo en el archivo `models.py` correspondiente.
2. **Detectar cambios:** Django analiza tus modelos y crea el archivo de migración automáticamente:
   ```bash
   python manage.py makemigrations
   ```
3. **Aplicar cambios:** Sincroniza la base de datos:
   ```bash
   python manage.py migrate
   ```

> [!IMPORTANT]
> **¿Cuándo borrar todo?** Solo hazlo en desarrollo si las migraciones entran en conflicto y no puedes resolverlo. En producción, **NUNCA** borres los archivos de migración ni la base de datos; siempre usa el flujo normal de `makemigrations` y `migrate`.

---

## 💳 Configuración de Stripe (Pasarela de Pagos)

El proyecto utiliza **Stripe** para procesar los pagos de la compra de boletos.

1. **Instalación de la dependencia:**
   La dependencia ya está incluida en `requirements.txt`. Si no la tienes instalada en tu entorno virtual, ejecútala con:
   ```bash
   pip install stripe
   ```

2. **Variables de Entorno necesarias:**
   Asegúrate de configurar las siguientes variables en tu archivo `.env` en la raíz de `backend/`:
   ```env
   STRIPE_PUBLIC_KEY=tu_clave_publica_de_stripe
   STRIPE_SECRET_KEY=tu_clave_secreta_de_stripe
   STRIPE_WEBHOOK_SECRET=tu_webhook_secret_de_stripe (opcional para desarrollo local)
   ```
