from django.db import models
from usuarios.models import SoftDeleteModel


class GeneroMusical(SoftDeleteModel):
    """Géneros musicales para clasificar a los artistas."""
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'generos_musicales'
        verbose_name = 'Género musical'
        verbose_name_plural = 'Géneros musicales'

    def __str__(self):
        return self.nombre
