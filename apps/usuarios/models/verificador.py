from django.db import models
from .base import SoftDeleteModel
from .usuario import Usuario
from .promotor import Promotor


class Verificador(SoftDeleteModel):
    """
    Perfil de verificador. Persona encargada de escanear y validar tickets
    en la entrada de los eventos. Creado y gestionado por un Promotor.
    """
    pago = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0,
        verbose_name='Pago',
        help_text='Monto de pago al verificador'
    )
    estado = models.CharField(
        max_length=50, default='activo',
        verbose_name='Estado',
        help_text='Estado del verificador: activo, inactivo, suspendido'
    )
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='perfil_verificador',
        verbose_name='Usuario'
    )
    promotor = models.ForeignKey(
        Promotor,
        on_delete=models.CASCADE,
        related_name='verificadores',
        null=True,
        blank=True,
        verbose_name='Promotor',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'verificadores'
        verbose_name = 'Verificador'
        verbose_name_plural = 'Verificadores'

    def __str__(self):
        return f"Verificador: {self.usuario.username} (Promotor: {self.promotor.razon_social}) - {self.estado}"
