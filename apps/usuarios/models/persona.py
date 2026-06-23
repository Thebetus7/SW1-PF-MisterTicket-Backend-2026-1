from django.db import models
from .base import SoftDeleteModel


class Persona(SoftDeleteModel):
    """
    Datos personales, separados del usuario para mantener 
    la responsabilidad única (SRP). Un usuario TIENE una persona.
    """
    nombre = models.CharField(max_length=255, verbose_name='Nombre completo')
    ci = models.CharField(
        max_length=20, unique=True,
        verbose_name='Cédula de identidad'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'personas'
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'

    def __str__(self):
        return f"{self.nombre} (CI: {self.ci})"
