from django.db import models
from usuarios.models import SoftDeleteModel
from .verificador_evento import VerificadorEvento


class RegistroAcceso(SoftDeleteModel):
    """
    Registro de cada intento de acceso/verificación de un ticket.
    Guarda si el acceso fue exitoso o no.
    """
    resultado = models.CharField(
        max_length=50,
        verbose_name='Resultado',
        help_text='aprobado, rechazado, ya_usado, invalido'
    )
    verificador_evento = models.ForeignKey(
        VerificadorEvento,
        on_delete=models.CASCADE,
        related_name='registros_acceso',
        verbose_name='Verificador del evento'
    )
    ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.CASCADE,
        related_name='registros_acceso',
        verbose_name='Ticket'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'registros_acceso'
        verbose_name = 'Registro de acceso'
        verbose_name_plural = 'Registros de acceso'

    def __str__(self):
        return f"Acceso {self.resultado} - Ticket #{self.ticket.id}"
