from django.db import models
from usuarios.models import SoftDeleteModel
from .zona import Zona


class Asiento(SoftDeleteModel):
    """
    Asiento individual dentro de una zona numerada.
    Solo aplica cuando zona.es_numerada = True.
    """
    fila = models.PositiveIntegerField(verbose_name='Fila')
    columna = models.PositiveIntegerField(verbose_name='Columna')
    estado = models.CharField(
        max_length=50, default='disponible',
        verbose_name='Estado',
        help_text='disponible, reservado, ocupado'
    )
    zona = models.ForeignKey(
        Zona,
        on_delete=models.CASCADE,
        related_name='asientos',
        verbose_name='Zona'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'asientos'
        verbose_name = 'Asiento'
        verbose_name_plural = 'Asientos'
        unique_together = ('fila', 'columna', 'zona')

    def __str__(self):
        return f"Fila {self.fila}, Col {self.columna} - {self.zona.nombre}"
