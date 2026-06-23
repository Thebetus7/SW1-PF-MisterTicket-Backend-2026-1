import uuid
from django.db import models
from usuarios.models import SoftDeleteModel


class Factura(SoftDeleteModel):
    """
    Factura de compra de tickets.
    Un cliente (usuario) puede tener múltiples facturas.
    """
    precio = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Precio total'
    )
    estado_pago = models.CharField(
        max_length=50, default='pendiente',
        verbose_name='Estado del pago',
        help_text='pendiente, pagado, reembolsado, cancelado, cancelada'
    )
    cliente = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        related_name='facturas',
        verbose_name='Cliente'
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name='Stripe PaymentIntent ID',
        help_text='ID del PaymentIntent de Stripe para trazabilidad'
    )
    codigo_transaccion_pasarela = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Código de transacción pasarela',
        help_text='UUID único enviado a Libélula como identificador de la deuda'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'facturas'
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'

    def __str__(self):
        return f"Factura #{self.id} - {self.cliente.username} - {self.estado_pago}"
