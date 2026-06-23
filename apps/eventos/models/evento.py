from django.db import models
from usuarios.models import SoftDeleteModel
from .lugar import Lugar


class Evento(SoftDeleteModel):
    """Evento musical organizado en la plataforma."""
    nombre = models.CharField(max_length=255, verbose_name='Nombre del evento')
    estado = models.CharField(
        max_length=50, default='borrador',
        verbose_name='Estado',
        help_text='borrador, publicado, en_curso, finalizado, cancelado'
    )
    lugar = models.ForeignKey(
        Lugar,
        on_delete=models.PROTECT,
        related_name='eventos',
        verbose_name='Lugar'
    )
    promotor = models.ForeignKey(
        'usuarios.Promotor',
        on_delete=models.PROTECT,
        related_name='eventos',
        verbose_name='Promotor'
    )
    fecha_inicio = models.DateTimeField(verbose_name='Fecha y hora de inicio', null=True, blank=True)
    fecha_fin = models.DateTimeField(verbose_name='Fecha y hora de fin', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'eventos'
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'

    def __str__(self):
        return f"{self.nombre} ({self.estado})"
