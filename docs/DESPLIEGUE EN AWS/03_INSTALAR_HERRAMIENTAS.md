# Paso 3: Instalar Docker, Buildx y Docker Compose en la EC2

Conéctate por SSH a la EC2 y ejecuta los pasos en orden.

### 3.1 — Instalar Docker y Git

```bash
# Actualizar el sistema
sudo dnf update -y

# Instalar Docker y Git
sudo dnf install docker git -y

# Iniciar Docker y habilitarlo al arranque del servidor
sudo systemctl start docker
sudo systemctl enable docker

# Permitir que ec2-user use Docker sin sudo
sudo usermod -aG docker ec2-user
```

> [!IMPORTANT]
> Para aplicar el grupo `docker` en tu sesión actual:
> 1. Cierra SSH con `exit` y vuelve a conectarte, **o**
> 2. Ejecuta: `newgrp docker`

### 3.2 — Instalar Docker Buildx (obligatorio en Amazon Linux 2023)

```bash
# Crear carpeta de plugins de Docker CLI
sudo mkdir -p /usr/local/lib/docker/cli-plugins

# Descargar Buildx 0.19.3
sudo curl -L "https://github.com/docker/buildx/releases/download/v0.19.3/buildx-v0.19.3.linux-amd64" \
  -o /usr/local/lib/docker/cli-plugins/docker-buildx

sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx
```

**Verificar que la versión es correcta** (debe ser **0.17.0 o superior**):

```bash
docker buildx version
```

Si aún muestra `0.12.1`, fuerza el plugin nuevo:

```bash
export DOCKER_CLI_PLUGIN_EXTRA_DIRS=/usr/local/lib/docker/cli-plugins
echo 'export DOCKER_CLI_PLUGIN_EXTRA_DIRS=/usr/local/lib/docker/cli-plugins' >> ~/.bashrc
docker buildx version
```

### 3.3 — Instalar Docker Compose

```bash
# Descargar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose

sudo chmod +x /usr/local/bin/docker-compose

# Verificar instalación completa
docker --version
docker-compose --version
docker buildx version
```

**Checklist antes de desplegar** (los tres deben responder sin error):

| Comando | Qué validar |
|---|---|
| `docker --version` | Docker instalado |
| `docker-compose --version` | Compose instalado |
| `docker buildx version` | Versión **≥ 0.17.0** |

---

> **Siguiente paso:** [04_DESPLEGAR_Y_VERIFICAR.md](./04_DESPLEGAR_Y_VERIFICAR.md)  
> **Volver al índice:** [00_RESUMEN_GENERAL.md](./00_RESUMEN_GENERAL.md)
