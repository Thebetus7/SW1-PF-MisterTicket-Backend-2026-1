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

> **Siguiente paso:** [07_APAGAR_SERVICIOS.md](./07_APAGAR_SERVICIOS.md)  
> **Volver al índice:** [00_RESUMEN_GENERAL.md](./00_RESUMEN_GENERAL.md)
