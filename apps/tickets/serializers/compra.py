from rest_framework import serializers
from ..models import Ticket, Factura
from eventos.models import Evento, Zona

METODOS_PAGO = ('stripe', 'libelula')


class CompraRequestSerializer(serializers.Serializer):
    evento_id = serializers.IntegerField(required=True)
    zona_id = serializers.IntegerField(required=True)
    cantidad = serializers.IntegerField(required=True, min_value=1)
    metodo_pago = serializers.ChoiceField(
        choices=METODOS_PAGO,
        required=True,
        help_text="'stripe' para pago sincrono, 'libelula' para pago via WebView",
    )
    # Solo requerido cuando metodo_pago == 'stripe'
    payment_method_id = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        max_length=255,
        help_text="ID del metodo de pago de Stripe (requerido si metodo_pago='stripe')",
    )
    # Solo relevante cuando metodo_pago == 'libelula'.
    # Se usa CharField (no URLField) para aceptar deep-links con esquemas
    # personalizados como miapp://pago-completado además de https://
    url_retorno = serializers.CharField(
        required=False,
        default='',
        allow_blank=True,
        help_text='URL o deep-link de retorno para la app movil tras pagar en el WebView',
    )

    def validate(self, data):
        evento_id = data.get('evento_id')
        zona_id = data.get('zona_id')
        cantidad = data.get('cantidad')
        metodo_pago = data.get('metodo_pago')

        # Validar dependencia: Stripe requiere payment_method_id
        if metodo_pago == 'stripe' and not data.get('payment_method_id'):
            raise serializers.ValidationError({
                'payment_method_id': "Este campo es requerido cuando metodo_pago es 'stripe'."
            })

        try:
            evento = Evento.objects.get(id=evento_id, estado='publicado')
        except Evento.DoesNotExist:
            raise serializers.ValidationError(
                {"evento_id": "El evento no existe o no esta publicado."}
            )

        try:
            # select_for_update previene race conditions al reservar entradas
            zona = Zona.objects.select_for_update().select_related('evento').get(id=zona_id, evento=evento)
        except Zona.DoesNotExist:
            raise serializers.ValidationError(
                {"zona_id": "La zona no pertenece a este evento o no existe."}
            )

        if zona.entradas_disponibles < cantidad:
            raise serializers.ValidationError({
                "cantidad": (
                    f"No hay suficientes entradas disponibles. "
                    f"Disponibles: {zona.entradas_disponibles}"
                )
            })

        data['evento'] = evento
        data['zona'] = zona
        return data


# ── Serializers de respuesta ──────────────────────────────────────────────────

class TicketCompradoSerializer(serializers.ModelSerializer):
    zona_nombre = serializers.CharField(source='zona.nombre', read_only=True)
    evento_nombre = serializers.CharField(source='zona.evento.nombre', read_only=True)
    evento_fecha = serializers.DateTimeField(source='zona.evento.fecha_inicio', read_only=True)
    asiento_detalle = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ('id', 'codigo_qr', 'zona_nombre', 'asiento_detalle',
                  'evento_nombre', 'evento_fecha')

    def get_asiento_detalle(self, obj):
        if obj.asiento:
            return {
                'id': obj.asiento.id,
                'fila': obj.asiento.fila,
                'columna': obj.asiento.columna,
            }
        return None


class CompraResponseSerializer(serializers.ModelSerializer):
    """Respuesta del flujo sincrono (Stripe): devuelve los tickets directamente."""
    factura_id = serializers.IntegerField(source='id', read_only=True)
    precio_total = serializers.DecimalField(
        source='precio', max_digits=10, decimal_places=2, read_only=True
    )
    tickets = TicketCompradoSerializer(many=True, read_only=True)

    class Meta:
        model = Factura
        fields = ('factura_id', 'estado_pago', 'precio_total',
                  'stripe_payment_intent_id', 'tickets')


class ReservaResponseSerializer(serializers.Serializer):
    """Respuesta del flujo asincrono (Libelula): devuelve la URL del WebView."""
    factura_id = serializers.IntegerField()
    codigo_transaccion_pasarela = serializers.UUIDField()
    precio_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    estado_pago = serializers.CharField()
    url_pasarela_pagos = serializers.URLField()
