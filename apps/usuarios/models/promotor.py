from django.db import models
from .base import SoftDeleteModel
from .usuario import Usuario


class Promotor(SoftDeleteModel):
    """
    Perfil de promotor de eventos (anteriormente organizador).
    Contiene datos fiscales y bancarios para liquidaciones.
    """
    razon_social = models.CharField(max_length=255, verbose_name='Razón social')
    nit_rfc = models.CharField(max_length=50, verbose_name='NIT/RFC')
    banco_nombre = models.CharField(max_length=100, verbose_name='Nombre del banco')
    cuenta_bancaria = models.CharField(max_length=50, verbose_name='Cuenta bancaria')

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='perfil_promotor',
        verbose_name='Usuario'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'promotores'
        verbose_name = 'Promotor'
        verbose_name_plural = 'Promotores'

    def __str__(self):
        return self.razon_social
