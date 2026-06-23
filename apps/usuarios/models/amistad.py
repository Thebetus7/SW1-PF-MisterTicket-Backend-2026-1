from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Q

Usuario = get_user_model()


class Amistad(models.Model):
    """
    Relación de amistad entre dos usuarios fan.
    Requiere solicitud y aceptación mutua para poder transferir tickets.
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]

    solicitante = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='amistades_enviadas',
        verbose_name='Solicitante',
    )
    receptor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='amistades_recibidas',
        verbose_name='Receptor',
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'amistades'
        unique_together = ('solicitante', 'receptor')
        verbose_name = 'Amistad'
        verbose_name_plural = 'Amistades'

    def __str__(self):
        return f"{self.solicitante.username} → {self.receptor.username} ({self.estado})"

    @classmethod
    def son_amigos(cls, usuario_a, usuario_b):
        """Retorna True si ambos usuarios tienen una amistad aceptada."""
        if usuario_a.id == usuario_b.id:
            return False
        return cls.objects.filter(
            Q(solicitante=usuario_a, receptor=usuario_b, estado='aceptada')
            | Q(solicitante=usuario_b, receptor=usuario_a, estado='aceptada')
        ).exists()

    def get_amigo(self, usuario):
        """Retorna el otro usuario de la amistad."""
        return self.receptor if self.solicitante_id == usuario.id else self.solicitante
