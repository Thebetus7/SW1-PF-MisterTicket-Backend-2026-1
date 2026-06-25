# Despliegue Backend (Django + PostgreSQL) en AWS — Resumen General

Esta guía describe cómo empaquetar y desplegar el backend de **MisterTicket** en AWS usando **Docker** y **Docker Compose**. Este enfoque aislará la aplicación (Django) y la base de datos (PostgreSQL) en contenedores independientes, dejando de depender de bases de datos externas como Neon.

---

## 📋 Flujo General de Despliegue

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. CONFIGURAR ARCHIVOS DEL PROYECTO                                 │
│    Dockerfile, docker-compose.yml (Django + Postgres)               │
│                              ↓                                      │
│ 2. CREAR INSTANCIA EC2                                              │
│    Configurar la máquina virtual en la consola de AWS               │
│                              ↓                                      │
│ 3. INSTALAR HERRAMIENTAS EN EL SERVIDOR                             │
│    Git, Docker, Buildx, Docker Compose                              │
│                              ↓                                      │
│ 4. DESPLEGAR Y VERIFICAR                                            │
│    Clonar repo, construir imagen, levantar contenedores y migrar    │
│                              ↓                                      │
│ 5. ACTUALIZAR (cada vez que haya cambios)                           │
│    git push → SSH → git pull → docker-compose up --build → migrate  │
│                              ↓                                      │
│ 6. APAGAR SERVICIOS (Evitar facturación)                            │
│    Detener/Terminar instancia y liberar recursos asociados          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estructura de esta Guía

| Archivo | Contenido |
|---|---|
| `00_RESUMEN_GENERAL.md` | **Este archivo.** Flujo general y estructura |
| `01_CONFIGURAR_PROYECTO.md` | Archivos de Configuración Requeridos (`Dockerfile`, `docker-compose.yml`) |
| `02_CREAR_INSTANCIA_EC2.md` | Crear y configurar la máquina virtual en AWS |
| `03_INSTALAR_HERRAMIENTAS.md` | Instalar Git, Docker, Buildx y Docker Compose en la EC2 |
| `04_DESPLEGAR_Y_VERIFICAR.md` | Clonar, construir, levantar y ejecutar migraciones. |
| `05_ACTUALIZAR_PRODUCCION.md` | Flujo para subir cambios nuevos desde tu PC al servidor |
| `06_APAGAR_SERVICIOS.md` | Detener/terminar recursos para evitar cobros de AWS |
| `07_CONFIGURAR_S3.md` | (Opcional) Configurar Amazon S3 para el almacenamiento de archivos e imágenes |

---

> **Siguiente paso:** Continúa con [01_CONFIGURAR_PROYECTO.md](./01_CONFIGURAR_PROYECTO.md)
