from django.db import models
from usuarios.models import SoftDeleteModel
from .evento import Evento


class Zona(SoftDeleteModel):
    """
    Zona dentro de un evento (VIP, General, Platea, etc.)
    es_numerada: indica si la zona tiene asientos numerados o es general.
    """
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio')
    capacidad_max = models.PositiveIntegerField(verbose_name='Capacidad máxima')
    entradas_disponibles = models.PositiveIntegerField(verbose_name='Entradas disponibles')
    es_numerada = models.BooleanField(
        default=False,
        verbose_name='¿Es numerada?',
        help_text='Si es True, la zona tiene asientos numerados'
    )
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='zonas',
        verbose_name='Evento'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'zonas'
        verbose_name = 'Zona'
        verbose_name_plural = 'Zonas'

    def __str__(self):
        return f"{self.nombre} - {self.evento.nombre}"
