from django.db import models
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class DispositivoUsuario(models.Model):
    """
    Almacena los tokens de registro de Firebase Cloud Messaging (FCM) 
    para poder enviar notificaciones push externas a los dispositivos del usuario.
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='dispositivos',
        verbose_name='Usuario'
    )
    fcm_token = models.TextField(unique=True, verbose_name='Token FCM')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')

    class Meta:
        db_table = 'dispositivos_usuario'
        verbose_name = 'Dispositivo de Usuario'
        verbose_name_plural = 'Dispositivos de Usuarios'

    def __str__(self):
        return f"{self.usuario.username} - {self.fcm_token[:20]}..."
