from django.db import models
from usuarios.models import SoftDeleteModel


class Liquidacion(SoftDeleteModel):
    """
    Liquidación de pagos al organizador después de un evento.
    Contiene el desglose de montos: ventas, comisión y pago neto.
    """
    monto_total_ventas = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name='Monto total de ventas'
    )
    monto_comision_plataforma = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name='Monto comisión plataforma'
    )
    monto_pago_promotor = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name='Monto pago al promotor'
    )
    referencia_bancaria = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name='Referencia bancaria',
        help_text='Referencia de la transferencia bancaria'
    )
    estado = models.CharField(
        max_length=50, default='pendiente',
        verbose_name='Estado',
        help_text='pendiente, procesando, completado, fallido'
    )
    evento = models.OneToOneField(
        'eventos.Evento',
        on_delete=models.PROTECT,
        related_name='liquidacion',
        verbose_name='Evento'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'liquidaciones'
        verbose_name = 'Liquidación'
        verbose_name_plural = 'Liquidaciones'

    def __str__(self):
        return f"Liquidación #{self.id} - {self.evento.nombre} - {self.estado}"
