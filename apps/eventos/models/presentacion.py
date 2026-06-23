from django.db import models
from usuarios.models import SoftDeleteModel
from .evento import Evento


class PresentacionEvento(SoftDeleteModel):
    """
    Presentación de un artista en un evento.
    Define el orden de aparición y la hora de inicio.
    """
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='presentaciones',
        verbose_name='Evento'
    )
    artista = models.ForeignKey(
        'usuarios.Artista',
        on_delete=models.CASCADE,
        related_name='presentaciones',
        verbose_name='Artista'
    )
    orden_aparicion = models.PositiveIntegerField(
        verbose_name='Orden de aparición',
        help_text='Número que indica el orden en que se presenta el artista'
    )
    tiempo_inicio = models.DateTimeField(
        verbose_name='Tiempo de inicio',
        help_text='Fecha y hora en que inicia la presentación'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'presentaciones_evento'
        verbose_name = 'Presentación de evento'
        verbose_name_plural = 'Presentaciones de evento'
        ordering = ['orden_aparicion']

    def __str__(self):
        return f"#{self.orden_aparicion} {self.artista.nombre_artistico} en {self.evento.nombre}"
