from django.db import models
from django.contrib.auth import get_user_model
from .promotor import Promotor

Usuario = get_user_model()


class SeguidorPromotor(models.Model):
    """
    Registra el seguimiento (promotor favorito) de un usuario hacia un promotor de eventos.
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='seguimientos_promotores',
        verbose_name='Usuario'
    )
    promotor = models.ForeignKey(
        Promotor,
        on_delete=models.CASCADE,
        related_name='seguidores',
        verbose_name='Promotor'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'seguidores_promotores'
        unique_together = ('usuario', 'promotor')
        verbose_name = 'Seguidor de Promotor'
        verbose_name_plural = 'Seguidores de Promotores'

    def __str__(self):
        return f"{self.usuario.username} sigue a {self.promotor.razon_social}"
