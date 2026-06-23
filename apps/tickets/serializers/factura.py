from rest_framework import serializers
from ..models import Factura


class FacturaSerializer(serializers.ModelSerializer):
    cliente_username = serializers.CharField(
        source='cliente.username', read_only=True
    )

    class Meta:
        model = Factura
        fields = (
            'id', 'precio', 'estado_pago',
            'cliente', 'cliente_username',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
