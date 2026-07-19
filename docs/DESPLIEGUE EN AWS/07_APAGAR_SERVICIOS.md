# Paso 7: Apagar Servicios (Evitar Facturación)

Si estás usando AWS para una presentación o entorno de pruebas y no necesitas que la aplicación esté funcionando todo el tiempo, debes **detener o terminar la instancia EC2** para evitar cargos adicionales.

### 7.1 Detener la Instancia (Recomendado para pausas temporales)

Si planeas volver a encender el proyecto más adelante:
1. Ve a la consola de AWS (EC2).
2. Selecciona tu instancia `misterticket-backend-docker`.
3. Haz clic en **Estado de la instancia** > **Detener instancia**.

*Nota: Al detenerla no te cobran por hora de cómputo, pero sí te cobran una tarifa mínima por el almacenamiento (el volumen EBS de 16 GB). Además, cuando la vuelvas a encender, la **IP pública cambiará** (a menos que uses una Elastic IP).*

### 7.2 Terminar la Instancia (Borrado definitivo)

Si el proyecto terminó y ya no necesitas nada:
1. Ve a la consola de AWS (EC2).
2. Selecciona tu instancia `misterticket-backend-docker`.
3. Haz clic en **Estado de la instancia** > **Terminar instancia**.

Esto borrará permanentemente la máquina virtual, su disco duro y todos los datos en ella (incluyendo la base de datos PostgreSQL local en el Docker).

---

> **Siguiente paso:** [08_ELIMINAR_RASTRO_DOCKER.md](./08_ELIMINAR_RASTRO_DOCKER.md)  
> **Volver al índice:** [00_RESUMEN_GENERAL.md](./00_RESUMEN_GENERAL.md)
