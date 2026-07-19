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
│ 3. CONFIGURAR ALMACENAMIENTO AWS S3                                 │
│    Crear bucket, configurar CORS de audio e IAM para Django         │
│                              ↓                                      │
│ 4. INSTALAR HERRAMIENTAS EN EL SERVIDOR                             │
│    Git, Docker, Buildx, Docker Compose                              │
│                              ↓                                      │
│ 5. DESPLEGAR Y VERIFICAR                                            │
│    Clonar repo, construir imagen, levantar contenedores y migrar    │
│                              ↓                                      │
│ 6. ACTUALIZAR (cada vez que haya cambios)                           │
│    git push → SSH → git pull → docker-compose up --build → migrate  │
│                              ↓                                      │
│ 7. APAGAR SERVICIOS (Evitar facturación)                            │
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
| `03_CONFIGURAR_S3.md` | Configurar bucket de Amazon S3, CORS de audio y usuario IAM |
| `04_INSTALAR_HERRAMIENTAS.md` | Instalar Git, Docker, Buildx y Docker Compose en la EC2 |
| `05_DESPLEGAR_Y_VERIFICAR.md` | Clonar, construir, levantar y ejecutar migraciones en AWS |
| `06_ACTUALIZAR_PRODUCCION.md` | Flujo para subir cambios nuevos desde tu PC al servidor |
| `07_APAGAR_SERVICIOS.md` | Detener/terminar recursos para evitar cobros de AWS |
| `08_ELIMINAR_RASTRO_DOCKER.md` | Limpiar contenedores, imágenes y volúmenes de Docker residuales |

---

> **Siguiente paso:** Continúa con [01_CONFIGURAR_PROYECTO.md](./01_CONFIGURAR_PROYECTO.md)
