# Paso 2: Crear la Instancia EC2 en AWS

1. **Nombre:** `misterticket-backend-docker`
2. **AMI:** **Amazon Linux 2023 AMI** (capa gratuita).
3. **Tipo de Instancia:** `t3.small` recomendado (2 GiB RAM) — `t2.micro` o `t3.micro` solo si vas justo en presupuesto.
4. **Par de claves (inicio de sesión - SSH):**
   * Haz clic en **"Crear un nuevo par de claves"** (si no tienes una).
   * Llámalo `misterticket-key`.
   * Tipo de clave: **RSA**. Formato de archivo: **`.pem`**.
   * Presiona **Crear**. Tu navegador descargará automáticamente el archivo `misterticket-key.pem`. **Guárdalo en un lugar seguro**, ya que lo usarás para conectarte por SSH.
5. **Configuraciones de red (Security Group):**
   - Permitir **SSH** (puerto `22`) desde tu IP o cualquier lugar (`0.0.0.0/0`).
   - Permitir **HTTP** (puerto `80`) desde cualquier lugar (`0.0.0.0/0`) (ya que Docker Compose mapeará el puerto 80 del servidor directamente al backend).
6. **Almacenamiento:** `16 GiB gp3` (más espacio para imágenes de eventos).

Anota la **IP pública** de tu nueva instancia.

---

> **Siguiente paso:** [03_CONFIGURAR_S3.md](./03_CONFIGURAR_S3.md)  
> **Volver al índice:** [00_RESUMEN_GENERAL.md](./00_RESUMEN_GENERAL.md)
