from django.db import models
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class Notificacion(models.Model):
    """
    Representa el historial interno de alertas enviadas a los usuarios (fans y artistas).
    """
    TIPO_CHOICES = [
        ('nuevo_evento', 'Nuevo Evento Publicado'),
        ('evento_artista', 'Artista Incluido en Evento'),
        ('ticket_recibido', 'Ticket Recibido'),
        ('solicitud_amistad', 'Solicitud de Amistad'),
    ]

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Usuario'
    )
    titulo = models.CharField(max_length=255, verbose_name='Título')
    mensaje = models.TextField(verbose_name='Mensaje')
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name='Tipo')
    leido = models.BooleanField(default=False, verbose_name='Leído')
    evento = models.ForeignKey(
        'eventos.Evento',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='notificaciones',
        verbose_name='Evento'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')

    class Meta:
        db_table = 'notificaciones'
        ordering = ['-created_at']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f"{self.usuario.username} - {self.titulo} - {'Leído' if self.leido else 'No leído'}"
