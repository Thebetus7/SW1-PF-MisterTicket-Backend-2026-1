from django.db import models
from usuarios.models import SoftDeleteModel


class Departamento(SoftDeleteModel):
    """Departamentos/regiones donde se realizan eventos."""
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'departamentos'
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'

    def __str__(self):
        return self.nombre
