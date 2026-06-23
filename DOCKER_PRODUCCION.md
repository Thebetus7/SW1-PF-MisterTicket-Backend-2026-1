# 🐳 Despliegue con Docker en AWS EC2 — Guía de Producción para MisterTicket

Esta guía cubre **todo el proceso de punta a punta**: qué configurar en la consola de **AWS** (EC2, S3, IAM, DNS, base de datos) y qué hacer **dentro del servidor** con **Docker**.

> **SO del servidor:** esta guía usa **Amazon Linux 2023** (usuario SSH `ec2-user`, paquetes con `dnf`). Si usas Ubuntu, sustituye `dnf` → `apt`, `ec2-user` → `ubuntu` y la config de Nginx por `sites-available`.

> Para MinIO solo en desarrollo local, consulta [`MINIO_LOCAL.md`](./MINIO_LOCAL.md).

---

## 🏗️ Arquitectura recomendada en AWS

```mermaid
flowchart LR
    Usuario --> Route53[Route 53 / DNS]
    Route53 --> EC2[EC2 + Docker + Nginx]
    EC2 --> S3[(S3 Bucket)]
    EC2 --> DB[(PostgreSQL RDS o Neon)]
    Libelula[Libélula Pagos] --> EC2
    Frontend[Next.js / Flutter] --> EC2
    Frontend --> S3
```

| Servicio AWS | Para qué sirve en MisterTicket |
|---|---|
| **EC2** | Servidor donde corre Docker (Django + Gunicorn + Nginx) |
| **S3** | Fotos de perfil, imágenes de eventos y archivos subidos |
| **IAM** | Permisos para que el backend acceda a S3 |
| **Security Group** | Firewall: abre 80/443, protege SSH y puerto 8000 |
| **Elastic IP** | IP fija para tu dominio (no cambia al reiniciar EC2) |
| **Route 53** (opcional) | DNS del dominio `api.misterticket.com` |
| **RDS** (opcional) | PostgreSQL gestionado por AWS (alternativa a Neon) |

---

## 📋 Checklist general (antes de empezar)

- [ ] Cuenta AWS activa con tarjeta de crédito/débito
- [ ] Dominio registrado (Route 53, GoDaddy, Namecheap, etc.)
- [ ] Repositorio del backend en GitHub/GitLab
- [ ] API Key de Libélula para producción
- [ ] Instancia EC2 con **Amazon Linux 2023** (región `us-east-2`)
- [ ] Credenciales del admin definidas (`DJANGO_SUPERUSER_*` en `.env.production`)
- [ ] `gunicorn`, `django-storages` y `boto3` en `requirements.txt` ✅

**Orden recomendado de trabajo:**

1. Configurar **S3 + IAM** en AWS (solo consola — sin archivos en el servidor)
2. Crear **EC2 + Security Group + Elastic IP**
3. Crear **RDS** o Neon → **anotar** credenciales de BD (aún no creas `.env`)
4. Configurar **DNS** apuntando al EC2
5. Conectarte por SSH → **git clone** → crear archivos → **ahí sí** `.env.production`
6. Desplegar con **Docker Compose + Nginx + HTTPS**

> [!NOTE]
> **Pasos 1–6 = consola AWS + anotar datos.** **Pasos 7–11 = servidor EC2 + archivos.** Si estás en el Paso 5 (RDS/Neon), todavía **no** necesitas el proyecto clonado en el EC2.

---

## 🗺️ ¿Dónde ocurre cada cosa? (mapa rápido)

| Qué | ¿Dónde? | ¿Cuándo? |
|---|---|---|
| S3, IAM, EC2, RDS, DNS | **Consola AWS** (navegador) | Pasos 1–6 |
| Anotar Endpoint, contraseña BD, etc. | **Bloc de notas / papel** | Al terminar Paso 5 |
| `git clone` del backend | **Servidor EC2** (SSH) | Paso 9 |
| `Dockerfile`, `docker-compose.prod.yml` | **EC2**, carpeta del repo clonado | Paso 9 |
| **`.env.production`** | **EC2**, misma carpeta que `manage.py` | **Paso 10** (después del clone) |
| Editar `settings.py` | **Tu PC** (repo local) → commit → pull en EC2 | Antes o después del clone (ver abajo) |

**Ruta del `.env.production` en el EC2** (después del Paso 9):

```
/home/ec2-user/misterticket-backend/.env.production
         ↑                   ↑
    usuario SSH         carpeta donde hiciste git clone
                         (debe contener manage.py)
```

**Flujo completo en orden:**

```
AWS Console (Pasos 1–6)     Anotas credenciales en un papel
        ↓
SSH al EC2 (Paso 7)
        ↓
git clone (Paso 9)          Aparecen manage.py, core/settings.py, etc.
        ↓
nano .env.production (Paso 10)   Pegas las credenciales que anotaste
        ↓
docker compose up (Paso 11)   Docker lee .env.production
```

**Sobre `settings.py`:** el código vive en **GitHub**. Lo editas en tu PC, haces push, y en el EC2 haces `git pull`. Las **contraseñas** no van en `settings.py` — van en `.env.production` (solo en el servidor, nunca en git). Si `settings.py` aún tiene credenciales fijas, cámbialo en tu PC **antes** de desplegar (ver Paso 10).

---

# ☁️ PARTE 1 — Configuración en AWS Console

---

## 🪣 Paso 1: Crear el Bucket S3

1. Entra a [AWS Console](https://console.aws.amazon.com/) y selecciona la región **`us-east-2` (Ohio)** — usa la misma región en EC2, S3 y RDS.
2. Busca el servicio **S3** → **Create bucket**
3. Configura:

| Campo | Valor recomendado |
|---|---|
| **Bucket name** | `misterticket-prod` (único a nivel global) |
| **AWS Region** | `us-east-2` |
| **Object Ownership** | ACLs enabled → Bucket owner preferred |
| **Block Public Access** | **Desmarcar** "Block all public access" (necesario para URLs públicas de imágenes) |

4. Clic en **Create bucket**

### 1.1 Bucket Policy (lectura pública de archivos)

1. Abre el bucket → pestaña **Permissions** → **Bucket policy** → **Edit**
2. Pega esto (cambia el nombre si usaste otro):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::misterticket-prod/*"
    }
  ]
}
```

3. **Save changes**

### 1.2 CORS del bucket (si el frontend carga imágenes directo desde S3)

En **Permissions** → **Cross-origin resource sharing (CORS)**:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedOrigins": [
      "https://misterticket.com",
      "https://www.misterticket.com",
      "https://api.misterticket.com"
    ],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

### 1.3 Versionado (recomendado)

En **Properties** → **Bucket Versioning** → **Enable**

---

## 👤 Paso 2: Crear permisos IAM para acceder a S3

Tienes **dos opciones**. La **Opción A (IAM Role)** es la más segura para EC2.

### Opción A — IAM Role para EC2 (✅ recomendado)

El contenedor Docker hereda permisos del servidor sin guardar `AWS_ACCESS_KEY_ID` en `.env`.

Necesitas crear **dos cosas** en IAM:
1. Una **política de permisos** (qué puede hacer el role con S3)
2. Un **role** que asocia esa política a tu instancia EC2

---

#### 2.A.1 Crear la política de permisos S3

Una **política** es la lista de acciones permitidas (subir/leer/borrar archivos en tu bucket).

1. Ve a **IAM** → menú lateral **Policies** → **Create policy**
2. Pestaña **JSON** → borra el contenido y pega:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "MisterTicketS3Access",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::misterticket-prod",
        "arn:aws:s3:::misterticket-prod/*"
      ]
    }
  ]
}
```

> Reemplaza `misterticket-prod` por el nombre real de tu bucket si es distinto.

3. Clic en **Next**
4. En **Policy name** escribe: `MisterTicketS3Policy`
5. Clic en **Create policy**

Listo — ya tienes la política guardada. **No crees el role aquí**, solo la política.

| Acción IAM | Para qué lo usa Django |
|---|---|
| `s3:PutObject` | Subir fotos de perfil, imágenes de eventos |
| `s3:GetObject` | Leer archivos ya subidos |
| `s3:DeleteObject` | Eliminar archivos al borrar registros |
| `s3:ListBucket` | Operaciones internas de boto3 sobre el bucket |

---

#### 2.A.2 Crear el Role y vincularlo a EC2

Un **Role** es como una "credencial" que se le asigna a tu servidor EC2. Django dentro de Docker usará ese role para hablar con S3 **sin** poner keys en el `.env`.

1. Ve a **IAM** → menú lateral **Roles** → **Create role**
2. Pantalla **Select trusted entity**:
   - **Trusted entity type**: elige **AWS service**
   - **Use case**: elige **EC2**
   - Clic en **Next**
3. Pantalla **Add permissions**:
   - En el buscador escribe `MisterTicketS3Policy`
   - Marca el checkbox de esa política (la que creaste en 2.A.1)
   - Clic en **Next**
4. Pantalla **Name, review, and create**:
   - **Role name**: escribe `MisterTicketEC2S3Role`
   - (Opcional) **Description**: `Permite a EC2 acceder al bucket S3 de MisterTicket`
   - Clic en **Create role**

**¿Qué acabas de hacer?** Creaste un "puesto de trabajo" llamado `MisterTicketEC2S3Role` que dice: *"cualquier instancia EC2 con este role puede usar la política MisterTicketS3Policy"*.

Para comprobarlo: **IAM** → **Roles** → abre `MisterTicketEC2S3Role` → pestaña **Permissions** → debe aparecer `MisterTicketS3Policy`.

---

#### 2.A.3 Asignar el role a tu instancia EC2

El role solo sirve si lo **conectas** a tu servidor:

**Si aún no creaste el EC2** (Paso 4 de esta guía):
- Al lanzar la instancia → sección **Advanced details**
- En **IAM instance profile** selecciona `MisterTicketEC2S3Role`

**Si el EC2 ya existe**:
1. **EC2** → **Instances** → selecciona tu instancia
2. **Actions** → **Security** → **Modify IAM role**
3. **IAM role**: elige `MisterTicketEC2S3Role` → **Update IAM role**

Con esto, Django en Docker obtiene permisos S3 automáticamente. **No pongas** `AWS_ACCESS_KEY_ID` ni `AWS_SECRET_ACCESS_KEY` en `.env.production`.

### Opción B — Usuario IAM con Access Keys (alternativa)

Úsala solo si no puedes usar IAM Role.

1. **IAM** → **Users** → **Create user** → nombre: `misterticket-s3-user`
2. Sin acceso a consola AWS (solo programático) → **Next**
3. **Permissions** → **Attach policies directly** → busca y marca **`MisterTicketS3Policy`** (la de 2.A.1)
4. **Next** → **Create user**
5. Abre el usuario → **Security credentials** → **Create access key**
6. Tipo: **Application running outside AWS** → guarda el `.csv`

| Variable en `.env.production` | Valor |
|---|---|
| `AWS_ACCESS_KEY_ID` | Access key ID del CSV |
| `AWS_SECRET_ACCESS_KEY` | Secret access key del CSV |

---

## 🔐 Paso 3: Crear Security Group (firewall)

1. Ve a **EC2** → **Security Groups** → **Create security group**
2. Configura:

| Campo | Valor |
|---|---|
| **Name** | `misterticket-backend-sg` |
| **Description** | Firewall backend MisterTicket |
| **VPC** | default (o tu VPC si ya tienes una) |

3. **Inbound rules** (reglas de entrada):

| Type | Port | Source | Para qué |
|---|---|---|---|
| SSH | 22 | **Tu IP pública** (`x.x.x.x/32`) | Conectarte por terminal |
| HTTP | 80 | `0.0.0.0/0` | Certbot + redirección HTTPS |
| HTTPS | 443 | `0.0.0.0/0` | API pública + callbacks Libélula |

> [!IMPORTANT]
> **No abras el puerto 8000** al mundo. Gunicorn/Docker debe escuchar solo en `127.0.0.1:8000` dentro del EC2. Nginx expone 443 hacia afuera.

4. **Outbound rules**: deja el default (All traffic → `0.0.0.0/0`) para que EC2 pueda hablar con S3, RDS, Neon, etc.
5. **Create security group**

---

## 🖥️ Paso 4: Lanzar la instancia EC2

1. **EC2** → **Instances** → **Launch instances**
2. Configura:

| Campo | Valor recomendado |
|---|---|
| **Name** | `misterticket-api-prod` |
| **AMI** | **Amazon Linux 2023** AMI (64-bit x86) |
| **Instance type** | `t3.small` (2 vCPU, 2 GB RAM) — `t3.micro` solo para pruebas |
| **Key pair** | Create new key pair → tipo `.pem` → descarga `misterticket-key.pem` |
| **Network settings** | Select existing → elige `misterticket-backend-sg` |
| **Storage** | 20–30 GB gp3 |

3. En **Advanced details**:
   - **IAM instance profile**: selecciona `MisterTicketEC2S3Role` (si usaste Opción A del Paso 2)
4. **Launch instance**

### 4.1 Asignar Elastic IP (IP fija)

Sin Elastic IP, la IP pública cambia cada vez que apagas/enciendes la instancia y rompes el DNS.

> **¿Qué es una Elastic IP?** Es una dirección IP pública fija de AWS que puedes “pegar” a tu EC2. Sin ella, cada reinicio te da otra IP y tu dominio deja de funcionar.

**Requisito:** tu instancia `misterticket-api-prod` debe estar en estado **En ejecución** (running) antes de asociar la IP.

---

#### Parte A — Reservar una IP nueva (Allocate)

Estás en la pantalla correcta: **EC2** → **Red y seguridad** → **Direcciones IP elásticas**.

1. Clic en el botón naranja **Asignar dirección IP elástica** (en inglés: *Allocate Elastic IP address*)
2. En la pantalla siguiente deja todo por defecto:
   - **Red**: Amazon VPC
   - **Dirección IPv4 pública**: Asignación de direcciones IPv4 de Amazon
3. Clic en **Asignar** (abajo a la derecha)

Vuelves a la tabla y ahora debe aparecer **una fila** con una IP, por ejemplo `3.148.12.34`, y en la columna **Instancia asociada** dirá **–** (aún no está ligada a ningún servidor).

---

#### Parte B — Vincular esa IP a tu EC2 (Associate)

1. **Marca el checkbox** de la fila de la IP que acabas de crear (clic en la fila o en el cuadrito a la izquierda)
2. Clic en **Acciones** (arriba) → **Asociar dirección IP elástica** (*Associate Elastic IP address*)
3. Completa el formulario:

| Campo en AWS (español) | Qué elegir |
|---|---|
| **Recurso** | Instancia |
| **Instancia** | `misterticket-api-prod` (o el ID `i-0abc123...`) |
| **Dirección IP privada** | Déjalo en automático (aparece solo una opción) |
| **Reasociación** | Marca la casilla si te la muestra (permite cambiar IP si ya tenía otra) |

4. Clic en **Asociar**

**Cómo saber que funcionó:** en la tabla, la columna **Instancia asociada** ya no dice **–**, sino el nombre `misterticket-api-prod` o su ID.

---

#### Parte C — Anotar la IP para DNS

Copia la IP de la columna **Dirección IPv4** (ej. `3.148.12.34`). La usarás en el **Paso 6** para crear el registro DNS:

```
api.misterticket.com  →  A  →  3.148.12.34
```

---

#### Si no ves tu instancia en el desplegable

- Verifica que estás en la región **`us-east-2`** (arriba a la derecha en la consola)
- La instancia debe estar **En ejecución**, no detenida
- Si aún no lanzaste el EC2, vuelve al **Paso 4** y créala primero

#### Si la instancia ya tenía otra IP pública

Al asociar la Elastic IP, AWS **reemplaza** la IP temporal anterior. Usa siempre la **Elastic IP** para DNS y SSH, no la vieja.

---

## 🗄️ Paso 5: Base de datos PostgreSQL

Elige **una** opción:

### Opción A — Neon (más simple, recomendado si nunca usaste AWS RDS)

**¿Qué es Neon?** Es PostgreSQL en la nube (como tener tu base de datos en un servidor externo). Tu EC2 solo se **conecta por internet** — no instalas Postgres en el servidor ni abres el puerto 5432 en el Security Group.

**Ventajas para MisterTicket:**
- Plan gratuito suficiente para empezar
- Misma tecnología que ya usa el proyecto (`psycopg2` + PostgreSQL)
- SSL incluido (Django ya lo requiere con `sslmode: require`)
- Backups automáticos por rama

---

#### 5.A.1 Crear cuenta y proyecto en Neon

1. Entra a [https://neon.tech](https://neon.tech) → **Sign up** (puedes usar GitHub o Google)
2. Tras el registro, Neon te pide crear un proyecto:
   - **Project name**: `misterticket` o `Neondb` (el nombre que quieras)
   - **Region**: elige **`AWS US East 2 (Ohio)`** — debe coincidir con tu EC2 (`us-east-2`)
   - **Postgres version**: deja la más reciente (16 o 17)
3. Clic en **Create project**

Neon crea automáticamente:
- Una **rama** llamada `main` o `Producción` (branch de base de datos)
- Un usuario owner (ej. `neondb_owner`)
- Una base de datos (ej. `neondb`)
- Un **endpoint** (host de conexión)

> [!TIP]
> En Neon, una **rama (branch)** es como una copia independiente de la BD. Usa la rama **Producción** para el servidor real y, si quieres, otra rama para desarrollo local.

---

#### 5.A.2 Obtener los datos de conexión (pantalla que ya tienes)

En el dashboard verás algo como **Resumen de la rama → Producción** con pestañas **Calcula**, **Roles y bases de datos**, etc.

**Forma más fácil — botón Conecta:**

1. En la tarjeta del endpoint (ej. `ep-morning-thunder-atfx1fuv`), clic en **Conecta**
2. Se abre un panel con la **connection string**. Elige:
   - **Branch**: `Producción` (o `main`)
   - **Database**: `neondb` (o el nombre que muestre)
   - **Role**: `neondb_owner`
3. Copia la cadena. Se ve así:

```
postgresql://neondb_owner:AbCdEf123456@ep-morning-thunder-atfx1fuv.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**Cómo traducir esa URL a tu `.env.production`:**

| Parte de la URL | Variable en `.env` | Ejemplo |
|---|---|---|
| Después del `://` y antes de `:` | `DB_USER` | `neondb_owner` |
| Entre `:` y `@` | `DB_PASSWORD` | `AbCdEf123456` |
| Después de `@` y antes de `/` | `DB_HOST` | `ep-morning-thunder-atfx1fuv.us-east-2.aws.neon.tech` |
| Después del último `/` y antes de `?` | `DB_NAME` | `neondb` |
| (siempre) | `DB_PORT` | `5432` |

**Forma alternativa — pestaña Roles y bases de datos:**

1. Clic en la pestaña **Roles y bases de datos**
2. Ahí ves el nombre de la BD, el usuario (role) y puedes **resetear la contraseña** si la perdiste
3. El host sigue siendo el endpoint de la pestaña **Calcula** (ej. `ep-morning-thunder-atfx1fuv.us-east-2.aws.neon.tech`)

---

#### 5.A.3 Anota estos valores de Neon (el archivo `.env` se crea después)

> **Todavía no creas ningún archivo.** Estás en la consola de Neon/AWS. Solo **copia estos datos** a un bloc de notas. El archivo `.env.production` lo crearás en el **Paso 10**, en el EC2, **después** de hacer `git clone`.

Valores que necesitarás pegar más adelante:

```env
# ─── Base de datos Neon (Producción) ──────────────────
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=la-contraseña-que-muestra-neon-al-crear-el-proyecto
DB_HOST=ep-morning-thunder-atfx1fuv.us-east-2.aws.neon.tech
DB_PORT=5432
```

> [!IMPORTANT]
> - La contraseña solo se muestra completa al **crear** el proyecto o al **resetear** el role en Neon. Si no la guardaste: **Roles y bases de datos** → tu role → **Reset password**.
> - **Nunca** subas el archivo `.env.production` a git (está en `.gitignore`).

**Sobre `settings.py`:** ese archivo está en el **repositorio** (`core/settings.py`). Debe **leer** las variables con `os.getenv('DB_NAME')`, etc. — no guardar contraseñas en el código. Si aún no clonaste el proyecto en el EC2, edítalo en **tu PC**, haz commit/push, y luego clonarás la versión correcta. Detalle en el **Paso 10**.

---

#### 5.A.4 SSL y acceso desde EC2

- Neon **exige SSL** → Django ya lo cubre con `'sslmode': 'require'`
- **No** necesitas configurar nada en el Security Group del EC2 para la BD
- El EC2 solo necesita **salida a internet** (outbound por defecto está abierto) hacia el host `*.neon.tech` puerto `5432`

En Neon → **Settings** del proyecto (icono engranaje):
- **IP Allow** (si aparece en tu plan): en el free tier suele estar abierto a cualquier IP; si activas restricción, agrega la **Elastic IP** de tu EC2

---

#### 5.A.5 Probar la conexión antes de Docker

Desde tu EC2 (después de conectarte por SSH), opcional pero recomendado:

```bash
# Instalar cliente postgres (Amazon Linux 2023)
sudo dnf install -y postgresql15

# Probar conexión (reemplaza con tus datos)
psql "postgresql://neondb_owner:TU_PASSWORD@ep-morning-thunder-atfx1fuv.us-east-2.aws.neon.tech/neondb?sslmode=require"
```

Si entras y ves el prompt `neondb=>`, la conexión funciona. Escribe `\q` para salir.

Desde Docker (cuando ya esté levantado):

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

Si `migrate` termina sin error, Django ya habla con Neon.

---

#### 5.A.6 Desarrollo local vs producción (recomendado)

| Entorno | Dónde | Rama Neon sugerida |
|---|---|---|
| Tu PC (desarrollo) | `.env` local | `development` o rama hija |
| EC2 (producción) | `.env.production` | `Producción` / `main` |

Para no mezclar datos de prueba con datos reales:

1. En Neon → **Create child branch** (rama hija) desde Producción, o crea otra rama `development`
2. Usa la connection string de **cada rama** en su entorno correspondiente
3. En local corres `seed_admin` y seeders de demo; en producción solo `seed_admin`

---

#### 5.A.7 Resumen rápido — qué anotar de Neon

| Dato | Dónde encontrarlo en Neon | ¿Lo tienes? |
|---|---|---|
| `DB_HOST` | Conecta → host / endpoint `ep-....neon.tech` | ☐ |
| `DB_USER` | Conecta → Role (ej. `neondb_owner`) | ☐ |
| `DB_PASSWORD` | Conecta o Reset password en Roles | ☐ |
| `DB_NAME` | Conecta → Database (ej. `neondb`) | ☐ |
| `DB_PORT` | Siempre `5432` | ☐ |
| Región | Dashboard del proyecto → `us-east-2` | ☐ |

**No necesitas abrir puertos extra en EC2** — Neon es un servicio externo al que tu servidor se conecta saliendo hacia internet.

### Opción B — Amazon RDS PostgreSQL (todo dentro de AWS)

**¿Qué es RDS?** Es PostgreSQL administrado por AWS en la misma nube que tu EC2. A diferencia de Neon, la base vive **dentro de tu VPC** y solo tu EC2 (con el firewall correcto) puede conectarse.

**Cuándo elegir RDS en vez de Neon:**
- Quieres todo en AWS (EC2 + S3 + RDS en `us-east-2`)
- Prefieres no depender de un servicio externo
- Tienes free tier de RDS disponible (12 meses en cuentas nuevas)

---

#### 5.B.1 Ir a la pantalla de creación

1. En la consola AWS, región **`us-east-2` (Ohio)** arriba a la derecha
2. Busca el servicio **RDS** → menú **Bases de datos** → botón naranja **Crear base de datos**

---

#### 5.B.2 Elegir método y motor (como en tu captura)

**Elegir un método de creación de base de datos**

| Opción | ¿Cuál marcar? |
|---|---|
| **Creación sencilla** | ✅ Recomendado para empezar (AWS preconfigura VPC, backups, etc.) |
| Creación estándar | Solo si necesitas control total de cada opción |

**Opciones del motor**

| Campo | Valor |
|---|---|
| **Tipo de motor** | **PostgreSQL** |
| **Versión del motor** | Deja la más reciente disponible (ej. PostgreSQL 16.x) |

---

#### 5.B.3 Plantilla y tamaño (capa gratuita)

**Plantillas**

| Opción | ¿Cuál marcar? |
|---|---|
| **Capa gratuita** | ✅ Si tu cuenta tiene free tier de RDS |
| Producción | Para tráfico real sin límites del free tier |

Con **Capa gratuita** AWS configura automáticamente:
- Clase: **`db.t3.micro`** (2 vCPU, 1 GiB RAM)
- Almacenamiento: **1 GiB** SSD gp2 (ampliable hasta 20 GiB)

> [!NOTE]
> `db.t3.micro` con 1 GiB RAM es suficiente para pruebas y demos. Para producción con muchos usuarios, más adelante escala a `db.t3.small` o superior.

---

#### 5.B.4 Configuración — campos que debes completar

| Campo en AWS (español) | Valor en tu captura | Qué es |
|---|---|---|
| **Identificador de instancias de base de datos** | `misterticket-prod` | Nombre interno del servidor RDS (no es el nombre de la BD) |
| **Nombre de usuario maestro** | `postgres` | Usuario administrador de PostgreSQL |
| **Administración de credenciales** | **Autoadministrada** | Tú defines la contraseña (no Secrets Manager) |
| **Contraseña maestra** | (la que elijas) | Mín. 8 caracteres — **guárdala ahora** |
| **Confirmar contraseña maestra** | (repetir) | Debe coincidir |

> [!IMPORTANT]
> Anota la contraseña en un lugar seguro. RDS **no** te la vuelve a mostrar completa después de crear la instancia.

**Sobre el identificador `misterticket-prod`:**
- Es el nombre del **recurso RDS** en la consola
- El **host de conexión** será algo como: `misterticket-prod.xxxxxxxxx.us-east-2.rds.amazonaws.com`
- No lo confundas con `DB_NAME` (nombre de la base de datos dentro de Postgres)

---

#### 5.B.5 Conectar el EC2 a RDS (muy importante)

En la sección **Configuración de la conexión de EC2 - opcional** (debajo de la contraseña):

1. Expande esa sección
2. Clic en **Configurar la conexión de EC2**
3. Selecciona tu instancia **`misterticket-api-prod`**
4. Confirma

**¿Qué hace esto?** AWS automáticamente:
- Pone RDS y EC2 en la **misma VPC**
- Crea/ajusta los **Security Groups** para que el EC2 pueda entrar al puerto **5432** de RDS
- Deja **Acceso público: No** (más seguro)

> Si **no** usas esta opción, tendrás que configurar Security Groups manualmente (paso 5.B.7).

Debajo puedes expandir **Ver la configuración predeterminada de la creación sencilla** para revisar VPC, subredes y backups automáticos (déjalos por defecto si no sabes qué cambiar).

---

#### 5.B.6 Crear y esperar

1. Marca la casilla de licencia al final de la página
2. Clic en **Crear base de datos**
3. Vuelves a la lista de bases de datos — el **Estado** será **Creando** durante **5–15 minutos**
4. Espera hasta que diga **Disponible** (verde)

No sigas con Docker hasta que esté **Disponible**.

---

#### 5.B.7 Security Group manual (solo si NO usaste "Conectar EC2")

Si saltaste la conexión automática con EC2:

1. **EC2** → **Security Groups** → busca el SG asociado a tu RDS (nombre tipo `rds-misterticket-prod` o similar)
2. **Edit inbound rules** → **Add rule**:

| Tipo | Puerto | Origen |
|---|---|---|
| PostgreSQL | 5432 | Security group del EC2 (`misterticket-backend-sg`) |

3. Guarda

---

#### 5.B.8 Obtener el Endpoint (host de conexión)

1. **RDS** → **Bases de datos** → clic en **`misterticket-prod`**
2. En **Conectividad y seguridad**, copia el **Endpoint**:

```
misterticket-prod.c1abc2def3ghi.us-east-2.rds.amazonaws.com
```

Ese valor completo es tu `DB_HOST`.

**Nombre de la base de datos (`DB_NAME`):**
- Con **Creación sencilla**, AWS crea por defecto una base llamada **`postgres`**
- Para verificar: en la instancia RDS → pestaña **Configuración** → busca **Nombre de base de datos inicial** o **DB name**

---

#### 5.B.9 Anota estos valores de RDS (el archivo `.env` se crea después)

> **Todavía no creas ningún archivo en el servidor.** Estás configurando RDS en la consola AWS. Solo **guarda estos datos** (bloc de notas). El archivo `.env.production` se crea en el **Paso 10**, en el EC2, **después** de `git clone`.

Con tu configuración (`postgres` + `misterticket-prod`), anota:

```env
# ─── Base de datos RDS (Producción) ───────────────────
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=la-contraseña-que-escribiste-al-crear-rds
DB_HOST=misterticket-prod.c1abc2def3ghi.us-east-2.rds.amazonaws.com
DB_PORT=5432
```

> Reemplaza `DB_HOST` por el **Endpoint real** de tu consola RDS (Paso 5.B.8). Cada cuenta tiene uno distinto.

**¿Dónde irá esto después?**

| Ahora (Paso 5) | Después (Paso 10 en EC2) |
|---|---|
| Anotas en bloc de notas | Pegas dentro de `/home/ec2-user/misterticket-backend/.env.production` |
| No existe el archivo aún | Misma carpeta que `manage.py` y `docker-compose.prod.yml` |
| No necesitas `git clone` todavía | Primero Paso 9 (`git clone`), luego Paso 10 (`nano .env.production`) |

**Sobre `settings.py`:** no lo editas en AWS. Está en el repo (`core/settings.py`). Las contraseñas van en `.env.production`, no en el código. Si `settings.py` tiene credenciales hardcodeadas, cámbialo en **tu PC** antes del despliegue — ver **Paso 10**.

---

#### 5.B.10 Probar la conexión desde el EC2

Conectado por SSH a tu EC2:

```bash
sudo dnf install -y postgresql15

psql -h misterticket-prod.c1abc2def3ghi.us-east-2.rds.amazonaws.com \
     -U postgres -d postgres -p 5432
```

Te pedirá la contraseña maestra. Si ves `postgres=>`, funciona. Escribe `\q` para salir.

Desde Docker (cuando esté levantado):

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

---

#### 5.B.11 Resumen — qué anotar de RDS

| Dato | Dónde encontrarlo | Ejemplo (tu captura) | ¿Lo tienes? |
|---|---|---|---|
| Identificador RDS | Lista de bases de datos | `misterticket-prod` | ☐ |
| `DB_HOST` | Conectividad → **Endpoint** | `misterticket-prod.xxx.us-east-2.rds.amazonaws.com` | ☐ |
| `DB_USER` | Configuración → usuario maestro | `postgres` | ☐ |
| `DB_PASSWORD` | La que definiste al crear | (solo tú la tienes) | ☐ |
| `DB_NAME` | BD inicial (creación sencilla) | `postgres` | ☐ |
| `DB_PORT` | Siempre | `5432` | ☐ |
| Estado | Lista de bases de datos | **Disponible** | ☐ |
| EC2 conectado | Creación o SG | `misterticket-api-prod` ↔ RDS puerto 5432 | ☐ |

---

#### 5.B.12 Errores frecuentes con RDS

| Error | Causa | Solución |
|---|---|---|
| `could not connect to server` | RDS aún creando o SG mal configurado | Espera **Disponible**; revisa SG puerto 5432 desde EC2 |
| `password authentication failed` | Contraseña incorrecta en `.env` | Verifica `DB_PASSWORD`; resetea en RDS → **Modificar** si hace falta |
| `timeout` | EC2 y RDS en VPC distintas | Usa **Configurar conexión de EC2** al crear o misma VPC |
| `database "misterticket_prod" does not exist` | `DB_NAME` incorrecto | Con creación sencilla suele ser `postgres`, no el identificador RDS |

---

## 🌍 Paso 6: Configurar DNS del dominio

Tu API debe responder en algo como `https://api.misterticket.com`.

### Con Route 53 (dominio en AWS)

1. **Route 53** → **Hosted zones** → tu dominio
2. **Create record**:
   - **Record name**: `api`
   - **Record type**: `A`
   - **Value**: Elastic IP del EC2 (ej. `54.123.45.67`)
   - **TTL**: 300
3. Save

### Con otro registrador (GoDaddy, Namecheap, etc.)

Crea un registro **A** en el panel DNS:

| Host | Type | Value |
|---|---|---|
| `api` | A | Elastic IP de tu EC2 |

Espera propagación DNS (5 min – 48 h). Verifica:

```bash
nslookup api.misterticket.com
```

---

## 📊 Resumen de lo que debes tener anotado de AWS

Antes de conectarte al EC2, confirma que tienes:

| Dato | Ejemplo | ¿Lo tienes? |
|---|---|---|
| Elastic IP del EC2 | `54.123.45.67` | ☐ |
| Archivo `.pem` del key pair | `misterticket-key.pem` | ☐ |
| Nombre bucket S3 | `misterticket-prod` | ☐ |
| Región AWS | `us-east-2` | ☐ |
| IAM Role o Access Keys S3 | `MisterTicketEC2S3Role` | ☐ |
| Endpoint PostgreSQL | Neon o RDS | ☐ |
| Dominio API | `api.misterticket.com` | ☐ |

---

# 🐳 PARTE 2 — Configuración en el servidor EC2 (Amazon Linux 2023)

Comandos de esta parte usan **`dnf`** (no `apt`) y el usuario **`ec2-user`**.

---

## 🔑 Paso 7: Conectarte por SSH al EC2

Desde tu PC (PowerShell / Git Bash):

```bash
# Dar permisos al .pem (Linux/Mac/Git Bash)
chmod 400 misterticket-key.pem

# Conectar (reemplaza IP y ruta del .pem)
ssh -i "misterticket-key.pem" ec2-user@54.123.45.67
```

En Windows PowerShell nativo también puedes usar:

```powershell
ssh -i "C:\ruta\misterticket-key.pem" ec2-user@54.123.45.67
```

> El usuario por defecto en **Amazon Linux 2023** es `ec2-user`. En Ubuntu sería `ubuntu`.

---

## 📦 Paso 8: Instalar Docker en el EC2 (Amazon Linux 2023)

Ya conectado por SSH como `ec2-user`:

```bash
sudo dnf update -y

# Docker Engine
sudo dnf install -y docker
sudo systemctl enable --now docker

# Permite usar docker sin sudo (requiere volver a entrar por SSH)
sudo usermod -aG docker ec2-user
```

Cierra la sesión SSH y vuelve a conectar (`exit` → `ssh ...`). Luego instala **Docker Compose** (plugin):

```bash
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

docker --version
docker compose version
```

Herramientas útiles para los siguientes pasos:

```bash
sudo dnf install -y git nano
```

---

## 📥 Paso 9: Clonar el proyecto y crear archivos Docker

```bash
git clone https://github.com/tu-usuario/misterticket-backend.git
cd misterticket-backend
```

### 9.1 Crear `Dockerfile`

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120"]
```

### 9.2 Crear `docker-compose.prod.yml`

```yaml
services:
  web:
    build: .
    container_name: misterticket_api
    restart: unless-stopped
    env_file:
      - .env.production
    ports:
      - "127.0.0.1:8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## ⚙️ Paso 10: Crear `.env.production` en el EC2

> **Prerrequisito:** ya hiciste el **Paso 9** (`git clone` + `cd` a la carpeta del proyecto). Si aún no clonaste, vuelve al Paso 9.

### Dónde y qué archivo crear

| | |
|---|---|
| **Ubicación** | Servidor EC2 (conectado por SSH) |
| **Ruta** | Carpeta raíz del backend clonado — la que contiene `manage.py` |
| **Ejemplo** | `/home/ec2-user/misterticket-backend/.env.production` |
| **En tu PC** | ❌ No lo crees aquí para subirlo a Git |
| **En Git** | ❌ Nunca — contiene contraseñas (`.gitignore` lo excluye) |

Comprueba que estás en la carpeta correcta:

```bash
pwd
ls manage.py core/settings.py
# Deben existir ambos archivos
```

Crea el archivo:

```bash
nano .env.production
```

Pega y completa con tus valores reales (incluye lo que **anotaste** en el Paso 5.A o 5.B):

```env
# ─── Django ───────────────────────────────────────────
SECRET_KEY=genera-clave-larga-con-openssl-rand-hex-32
DEBUG=False
ALLOWED_HOSTS=api.misterticket.com,54.123.45.67

# ─── Base de datos (RDS — Paso 5.B) ───────────────────
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=la-contraseña-maestra-de-rds
DB_HOST=misterticket-prod.xxxx.us-east-2.rds.amazonaws.com
DB_PORT=5432

# Si usas Neon en vez de RDS (Paso 5.A), reemplaza por:
# DB_NAME=neondb
# DB_USER=neondb_owner
# DB_HOST=ep-xxxx.us-east-2.aws.neon.tech
```

Guarda en nano: `Ctrl+O` → Enter → `Ctrl+X`.

Protege el archivo:

```bash
chmod 600 .env.production
```

### Cómo se relacionan `.env.production` y `settings.py`

Son **dos archivos distintos** con roles distintos:

```
.env.production          settings.py (core/settings.py)
─────────────────        ─────────────────────────────
Solo en el EC2           En el repo Git (tu PC → GitHub → EC2)
Contraseñas y secretos   Código que LEE esas variables
NO va a git              Sí va a git (sin contraseñas)
Lo creas en Paso 10      Ya existe al hacer git clone
```

Docker Compose inyecta `.env.production` en el contenedor (`env_file` en `docker-compose.prod.yml`). Django debe leerlas así en `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {'sslmode': 'prefer'},
    }
}

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')
```

> [!IMPORTANT]
> Si `settings.py` todavía tiene `PASSWORD` o `HOST` fijos en el código, edítalo en **tu PC**, haz `git push`, y en el EC2 ejecuta `git pull` **antes** de `docker compose up`. Sin eso, `.env.production` no tendrá efecto en la base de datos.

Resto del `.env.production` (S3, Libélula, CORS) — agrégalo al mismo archivo:

```env
# ─── AWS S3 ───────────────────────────────────────────
USE_S3=True
AWS_STORAGE_BUCKET_NAME=misterticket-prod
AWS_S3_REGION_NAME=us-east-2
# NO definir AWS_S3_ENDPOINT_URL con S3 real de AWS

# Solo si NO usaste IAM Role en EC2 (Opción B del Paso 2):
# AWS_ACCESS_KEY_ID=AKIA...
# AWS_SECRET_ACCESS_KEY=...

# ─── Libélula ─────────────────────────────────────────
LIBELULA_API_KEY=tu-api-key-real
BACKEND_BASE_URL=https://api.misterticket.com

# ─── CORS ─────────────────────────────────────────────
CORS_ALLOWED_ORIGINS=https://misterticket.com,https://www.misterticket.com

# ─── Admin (seed_admin — Paso 13) ─────────────────────
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@misterticket.com
DJANGO_SUPERUSER_PASSWORD=contraseña-segura-del-admin
```

Generar `SECRET_KEY` en el EC2:

```bash
openssl rand -hex 32
```

Pega el resultado en `SECRET_KEY=` dentro de `.env.production`.

---

## 🚀 Paso 11: Levantar Docker en producción

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml logs -f web
```

Comandos útiles:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml restart web
docker compose -f docker-compose.prod.yml down
```

---

## 🌐 Paso 12: Nginx + HTTPS (Let's Encrypt) — Amazon Linux 2023

El Security Group ya tiene 80 y 443 abiertos. Configura Nginx **en el EC2** (fuera de Docker):

```bash
sudo dnf install -y nginx certbot python3-certbot-nginx
sudo systemctl enable --now nginx
```

> Si `python3-certbot-nginx` no está en los repos: `sudo python3 -m pip install certbot certbot-nginx`

En Amazon Linux, la config va en **`/etc/nginx/conf.d/`** (no en `sites-available`):

```bash
sudo nano /etc/nginx/conf.d/misterticket.conf
```

Contenido:

```nginx
server {
    listen 80;
    server_name api.misterticket.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 20M;
    }
}
```

Activa la config y obtén SSL:

```bash
sudo nginx -t
sudo systemctl reload nginx

sudo certbot --nginx -d api.misterticket.com
```

Certbot renueva automáticamente. Verifica:

```bash
sudo certbot renew --dry-run
```

---

## 🔄 Paso 13: Migraciones, seeders y despliegues futuros

### ¿Qué se ejecuta automáticamente al levantar Docker?

El `Dockerfile` ya incluye `python manage.py migrate --noinput` al arrancar el contenedor.  
**Los seeders no se ejecutan solos** — debes lanzarlos manualmente la primera vez (o cuando lo necesites).

### Seeders disponibles en el proyecto

| Comando | Qué crea | ¿Producción? |
|---|---|---|
| `seed_admin` | Superusuario admin + usuarios de prueba (fan, artista, promotor, verificador) | ✅ Solo el admin (con variables de entorno) |
| `seeder_eventos` | Departamentos, lugares, 2 eventos publicados con zonas y asientos | ⚠️ Solo staging/demo |
| `seeder_add_artistas` | 15 artistas de prueba con géneros musicales | ⚠️ Solo staging/demo |

> [!IMPORTANT]
> **En producción real** ejecuta únicamente `seed_admin` para crear el administrador.  
> Los seeders de eventos y artistas insertan **datos de prueba** — no los uses en un entorno productivo con usuarios reales.

### Orden de ejecución (respetar dependencias)

`seeder_eventos` requiere que existan promotores → primero `seed_admin`.

```
migrate  →  seed_admin  →  seeder_eventos  →  seeder_add_artistas
                ↑                                    ↑
           obligatorio                         opcional (demo)
           en producción
```

### 13.1 Migraciones (manual, si hace falta)

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### 13.2 Seeder de admin — obligatorio en el primer despliegue

Define credenciales seguras en `.env.production` **antes** de ejecutar:

```env
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@misterticket.com
DJANGO_SUPERUSER_PASSWORD=una-contraseña-muy-segura-aqui
```

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py seed_admin
```

Esto crea el superusuario con las variables anteriores. Si no las defines, usa los defaults del comando (`admin` / `admin123`) — **cámbialos en producción**.

> Alternativa manual sin seeder: `python manage.py createsuperuser` (interactivo).

### 13.3 Seeders de demo — solo staging o pruebas en EC2

```bash
# Departamentos, lugares, eventos y asientos de ejemplo
docker compose -f docker-compose.prod.yml exec web python manage.py seeder_eventos

# 15 artistas de prueba con géneros musicales
docker compose -f docker-compose.prod.yml exec web python manage.py seeder_add_artistas
```

Los seeders son **idempotentes**: si vuelves a ejecutarlos, no duplican registros que ya existen (muestran advertencias y continúan).

### 13.4 Script completo — primer despliegue en producción

```bash
# 1. Levantar contenedor (migrate corre solo al arrancar)
docker compose -f docker-compose.prod.yml up -d

# 2. Crear admin de producción
docker compose -f docker-compose.prod.yml exec web python manage.py seed_admin
```

### 13.5 Script completo — entorno de demo/staging en EC2

```bash
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec web python manage.py seed_admin
docker compose -f docker-compose.prod.yml exec web python manage.py seeder_eventos
docker compose -f docker-compose.prod.yml exec web python manage.py seeder_add_artistas
```

### Actualizar código en producción

```bash
git pull origin main
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```

---

# ✅ PARTE 3 — Verificación final

---

## Paso 14: Comprobar que todo funciona

### 14.1 Contenedor Docker

```bash
docker compose -f docker-compose.prod.yml ps
```

Estado esperado: `running` o `healthy`.

### 14.2 API local en EC2

```bash
curl -I http://127.0.0.1:8000/api/
```

### 14.3 API pública con HTTPS

```bash
curl -I https://api.misterticket.com/api/
```

### 14.4 S3 desde el contenedor

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py shell
```

```python
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

print(default_storage.__class__)
path = default_storage.save('test/hello.txt', ContentFile(b'Hola S3 desde EC2'))
print(default_storage.url(path))
```

Abre la URL impresa en el navegador. Debe verse el texto y la URL debe ser de S3:

```
https://misterticket-prod.s3.us-east-2.amazonaws.com/test/hello.txt
```

### 14.5 Subida real por API

```http
PUT /api/usuarios/perfil/
Authorization: Bearer <token>
Content-Type: multipart/form-data

foto: <imagen>
```

Respuesta esperada:

```json
{
  "foto": "https://misterticket-prod.s3.us-east-2.amazonaws.com/usuarios/fotos/1/foto.jpg"
}
```

### 14.6 Callback de Libélula

- `BACKEND_BASE_URL=https://api.misterticket.com`
- Security Group con puerto **443** abierto
- Nginx reenviando `/api/pagos/...` al contenedor

---

## 🔒 Seguridad en AWS + Docker

| Práctica | Dónde configurarlo |
|---|---|
| SSH solo desde tu IP | Security Group inbound 22 |
| No exponer puerto 8000 | `127.0.0.1:8000` en docker-compose |
| IAM Role en EC2 (sin keys en .env) | IAM + EC2 instance profile |
| `DEBUG=False` | `.env.production` |
| HTTPS obligatorio | Certbot + Nginx |
| RDS sin acceso público | RDS → Public access: No |
| Rotar secretos cada 90 días | IAM keys, DB password, SECRET_KEY |
| Backups RDS | RDS → Automated backups (7–35 días) |
| Versionado S3 | Bucket → Versioning enabled |
| `.env.production` con chmod 600 | Solo en el EC2, nunca en git |

---

## 🛠️ Troubleshooting

### `sudo: apt: command not found`

Estás en **Amazon Linux 2023**, que usa **`dnf`**, no `apt`. Equivalencias:

| Ubuntu (`apt`) | Amazon Linux 2023 (`dnf`) |
|---|---|
| `sudo apt update` | `sudo dnf update -y` |
| `sudo apt install postgresql-client` | `sudo dnf install -y postgresql15` |
| `sudo apt install nginx` | `sudo dnf install -y nginx` |
| `curl get.docker.com` | `sudo dnf install -y docker` |

### No puedo conectar por SSH

- Verifica Security Group: puerto 22 solo desde **tu IP actual**
- Verifica que usas el usuario **`ec2-user`** (Amazon Linux) y el `.pem` correcto
- Verifica que la instancia está `running`

### `DisallowedHost`

Agrega el dominio a `ALLOWED_HOSTS` en `.env.production` y reinicia:

```bash
docker compose -f docker-compose.prod.yml restart web
```

### Error de conexión a PostgreSQL

- **RDS**: el SG de RDS debe permitir 5432 desde el SG del EC2
- **Neon**: verifica host, password y `sslmode=require`
- Revisa logs: `docker compose -f docker-compose.prod.yml logs web`

### Archivos no suben a S3 (`AccessDenied`)

- Confirma bucket policy y que Block Public Access está desactivado para lectura
- Si usas IAM Role: verifica que el role está asociado a la instancia EC2
- Si usas Access Keys: verifica `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY`
- Región correcta: `AWS_S3_REGION_NAME=us-east-2`

### Certbot falla

- El registro DNS `api` debe apuntar al Elastic IP **antes** de ejecutar certbot
- Puerto 80 debe estar abierto en Security Group
- Verifica: `nslookup api.misterticket.com`

### Libélula no llega al callback

- `BACKEND_BASE_URL` debe ser HTTPS público, no `localhost`
- Prueba manualmente: `curl https://api.misterticket.com/api/pagos/...`

---

## 📦 Mapa de archivos del proyecto

| Archivo | Dónde se crea | Propósito |
|---|---|---|
| `Dockerfile` | EC2 / repo | Imagen Django + Gunicorn |
| `docker-compose.prod.yml` | EC2 / repo | Orquestación producción |
| `.env.production` | Solo en EC2 | Secretos y config (no versionar) |
| `docker-compose-minio.yml` | Repo (local) | MinIO para desarrollo |
| `misterticket-key.pem` | Tu PC | Acceso SSH (no subir a git) |

---

## 🔗 Flujo completo resumido

```
AWS Console                          EC2 (SSH)
───────────                          ─────────
1. S3 bucket + policy        →       8. Instalar Docker
2. IAM Role / usuario S3     →       9. Clonar repo + Dockerfile
3. Security Group            →      10. .env.production
4. EC2 + Elastic IP          →      11. docker compose up -d
5. RDS o Neon                →      12. Nginx + Certbot
6. DNS → Elastic IP          →      13. seed_admin (+ seeders demo si aplica)
7. Anotar credenciales       →      14. Verificar API + S3 + Libélula
```

Para detalle adicional solo de S3 (migración de archivos locales, verificación avanzada), consulta también [`S3_PRODUCCION.md`](./S3_PRODUCCION.md).
