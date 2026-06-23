from rest_framework import serializers
from ..models import Lugar


class LugarSerializer(serializers.ModelSerializer):
    departamento_nombre = serializers.CharField(
        source='departamento.nombre', read_only=True
    )

    class Meta:
        model = Lugar
        fields = (
            'id', 'nombre', 'direccion', 'capacidad_total',
            'departamento', 'departamento_nombre',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
