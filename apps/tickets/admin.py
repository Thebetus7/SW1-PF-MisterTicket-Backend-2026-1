from django.contrib import admin
from .models import Factura, Ticket


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('id', 'precio', 'estado_pago', 'cliente', 'created_at', 'is_deleted')
    search_fields = ('cliente__username',)
    list_filter = ('estado_pago', 'deleted_at')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo_qr', 'estado', 'propietario', 'transferido', 'zona', 'asiento', 'factura', 'is_deleted')
    search_fields = ('codigo_qr', 'propietario__username')
    list_filter = ('estado', 'transferido', 'deleted_at')
