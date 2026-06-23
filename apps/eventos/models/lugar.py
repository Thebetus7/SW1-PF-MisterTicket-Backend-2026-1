from django.db import models
from usuarios.models import SoftDeleteModel
from .departamento import Departamento


class Lugar(SoftDeleteModel):
    """Lugar físico donde se realizan los eventos."""
    nombre = models.CharField(max_length=255, verbose_name='Nombre')
    direccion = models.TextField(verbose_name='Dirección')
    capacidad_total = models.PositiveIntegerField(verbose_name='Capacidad total')
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        related_name='lugares',
        verbose_name='Departamento'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lugares'
        verbose_name = 'Lugar'
        verbose_name_plural = 'Lugares'

    def __str__(self):
        return f"{self.nombre} - {self.departamento.nombre}"
