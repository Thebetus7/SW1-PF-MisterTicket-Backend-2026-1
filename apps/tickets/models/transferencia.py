from django.db import models
from django.contrib.auth import get_user_model
from .ticket import Ticket

Usuario = get_user_model()


class TransferenciaTicket(models.Model):
    """
    Registro de auditoría de transferencias de tickets entre usuarios.
    """
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.PROTECT,
        related_name='transferencias',
        verbose_name='Ticket',
    )
    origen = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='transferencias_enviadas',
        verbose_name='Usuario origen',
    )
    destino = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='transferencias_recibidas',
        verbose_name='Usuario destino',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transferencias_tickets'
        verbose_name = 'Transferencia de Ticket'
        verbose_name_plural = 'Transferencias de Tickets'
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket {self.ticket.codigo_qr}: {self.origen.username} → {self.destino.username}"
