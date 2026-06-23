from rest_framework import serializers
from ..models import Zona, Asiento


class ZonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zona
        fields = (
            'id', 'nombre', 'precio', 'capacidad_max',
            'entradas_disponibles', 'es_numerada',
            'evento', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class AsientoSerializer(serializers.ModelSerializer):
    zona_nombre = serializers.CharField(source='zona.nombre', read_only=True)

    class Meta:
        model = Asiento
        fields = (
            'id', 'fila', 'columna', 'estado',
            'zona', 'zona_nombre',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
