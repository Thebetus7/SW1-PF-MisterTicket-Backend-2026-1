from django.db import models
from usuarios.models import SoftDeleteModel
from .evento import Evento


class VerificadorEvento(SoftDeleteModel):
    """
    Relación entre un verificador y un evento.
    Un verificador puede estar asignado a múltiples eventos.
    """
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='verificadores_evento',
        verbose_name='Evento'
    )
    verificador = models.ForeignKey(
        'usuarios.Verificador',
        on_delete=models.CASCADE,
        related_name='eventos_asignados',
        verbose_name='Verificador'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'verificadores_evento'
        verbose_name = 'Verificador de evento'
        verbose_name_plural = 'Verificadores de evento'
        unique_together = ('evento', 'verificador')

    def __str__(self):
        return f"{self.verificador} → {self.evento.nombre}"
