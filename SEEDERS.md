# 🚀 MisterTicket Backend - Guía de Seeders y Comandos

Este documento recopila la lista de todos los comandos y seeders personalizados de Django disponibles en el backend de MisterTicket para poblar la base de datos y realizar tareas de mantenimiento.

---

## 1. Comandos de Poblado de Datos (Seeders)

Para poblar tu base de datos de PostgreSQL desde cero, debes ejecutar los siguientes comandos en orden secuencial:

### 1️⃣ `python manage.py seed_admin`
* **Ubicación:** `apps/usuarios/management/commands/seed_admin.py`
* **Descripción:** 
  * Crea los grupos y roles predeterminados del sistema: **Administrador**, **Cliente (Fan)**, **Promotor** y **Verificador**.
  * Genera el superusuario administrador inicial en base a las variables de entorno o credenciales por defecto:
    * **Email:** `admin@misterticket.com`
    * **Password:** `Admin123*` (o la configurada en tu `.env`).
* **Uso:**
  ```bash
  python manage.py seed_admin
  ```

### 2️⃣ `python manage.py seeder_add_artistas`
* **Ubicación:** `apps/usuarios/management/commands/seeder_add_artistas.py`
* **Descripción:** 
  * Registra **15 artistas de ejemplo** en el sistema para simular el catálogo musical de la red social.
  * Asocia a cada artista con su biografía, géneros sugeridos y perfiles listos para recibir canciones o ser asignados a presentaciones de conciertos.
* **Uso:**
  ```bash
  python manage.py seeder_add_artistas
  ```

### 3️⃣ `python manage.py seeder_eventos`
* **Ubicación:** `apps/eventos/management/commands/seeder_eventos.py`
* **Descripción:** 
  * Inserta los departamentos predeterminados (ej. La Paz, Santa Cruz, Cochabamba, etc.).
  * Registra locaciones físicas o lugares de eventos (ej. *Estadio Hernando Siles*, *Fexpocruz*).
  * Crea **2 eventos musicales de ejemplo** con sus respectivas zonas de precios, disponibilidad de asientos y fechas de presentación.
* **Uso:**
  ```bash
  python manage.py seeder_eventos
  ```

---

## 2. Comandos de Inteligencia Artificial (IA)

### 🤖 `python manage.py train_classifier`
* **Ubicación:** `apps/musica/management/commands/train_classifier.py`
* **Descripción:** 
  * Genera un dataset sintético calibrado con patrones de ondas de audio físicas reales (BPM, Energía RMS, Brillo de Frecuencia y 13 coeficientes MFCC) para géneros como Rock, Pop, Reggaeton, Electrónica, Jazz y Baladas.
  * Entrena localmente un modelo de clasificación **RandomForest** de `scikit-learn`.
  * Guarda el modelo serializado en `core/ia_models/genero_classifier.joblib` para ser usado de forma offline en la clasificación de audios subidos al backend.
* **Uso:**
  ```bash
  python manage.py train_classifier
  ```

---

## 3. Comandos de Mantenimiento y Cronjobs

### 🧹 `python manage.py limpiar_reservas`
* **Ubicación:** `apps/tickets/management/commands/limpiar_reservas.py`
* **Descripción:** 
  * Analiza la base de datos buscando reservas de boletos en estado "Pendiente" que hayan superado el tiempo límite de espera de pago sin concretar la compra.
  * Libera automáticamente los asientos y cambia el estado de las reservas a "Expirado" para reintroducirlos al stock de entradas disponibles.
* **Uso:**
  ```bash
  python manage.py limpiar_reservas
  ```
