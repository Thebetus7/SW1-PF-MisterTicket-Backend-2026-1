from rest_framework import serializers
from ..models import Liquidacion


class LiquidacionSerializer(serializers.ModelSerializer):
    evento_nombre = serializers.CharField(source='evento.nombre', read_only=True)

    class Meta:
        model = Liquidacion
        fields = (
            'id',
            'monto_total_ventas',
            'monto_comision_plataforma',
            'monto_pago_promotor',
            'referencia_bancaria',
            'estado',
            'evento', 'evento_nombre',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
