from django.contrib import admin
from .models import Liquidacion


@admin.register(Liquidacion)
class LiquidacionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'evento', 'monto_total_ventas', 'monto_comision_plataforma',
        'monto_pago_promotor', 'estado', 'created_at', 'is_deleted'
    )
    search_fields = ('evento__nombre', 'referencia_bancaria')
    list_filter = ('estado', 'deleted_at')
