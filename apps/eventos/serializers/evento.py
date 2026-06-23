from rest_framework import serializers
from ..models import Evento, Zona, Asiento, PresentacionEvento
from .zona_asiento import ZonaSerializer


# --- SERIALIZERS DE SOPORTE PARA ELENCO Y PRESENTACIONES ---

class ArtistaFeedSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre_artistico = serializers.CharField()
    biografia = serializers.CharField()
    foto_url = serializers.CharField()
    departamento_origen_nombre = serializers.CharField(source='departamento_origen.nombre', default=None, read_only=True)
    popularidad = serializers.IntegerField()
    generos_musicales_nombres = serializers.SerializerMethodField()

    def get_generos_musicales_nombres(self, obj):
        return [g.nombre for g in obj.generos_musicales.all()]


class PresentacionFeedSerializer(serializers.ModelSerializer):
    artista = ArtistaFeedSerializer(read_only=True)

    class Meta:
        model = PresentacionEvento
        fields = ('id', 'artista', 'orden_aparicion', 'tiempo_inicio')


class EventoSerializer(serializers.ModelSerializer):
    lugar_nombre = serializers.CharField(source='lugar.nombre', read_only=True)
    promotor_razon = serializers.CharField(
        source='promotor.razon_social', read_only=True
    )
    zonas = ZonaSerializer(many=True, read_only=True)
    presentaciones = PresentacionFeedSerializer(many=True, read_only=True)

    class Meta:
        model = Evento
        fields = (
            'id', 'nombre', 'estado',
            'lugar', 'lugar_nombre',
            'promotor', 'promotor_razon',
            'zonas',
            'presentaciones',
            'fecha_inicio', 'fecha_fin',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'promotor')


class ZonaCrearSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=100)
    precio = serializers.DecimalField(max_digits=10, decimal_places=2)
    cantidad_asientos = serializers.IntegerField(min_value=1)


class EventoCrearSerializer(serializers.ModelSerializer):
    zonas = ZonaCrearSerializer(many=True, write_only=True)

    class Meta:
        model = Evento
        fields = ('id', 'nombre', 'estado', 'lugar', 'fecha_inicio', 'fecha_fin', 'zonas')

    def validate(self, data):
        lugar = data.get('lugar')
        zonas = data.get('zonas', [])

        if not zonas:
            raise serializers.ValidationError({"zonas": "Debes crear al menos una zona."})

        total_asientos = sum(z['cantidad_asientos'] for z in zonas)
        if total_asientos > lugar.capacidad_total:
            raise serializers.ValidationError({
                "zonas": f"La suma de asientos ({total_asientos}) excede "
                         f"la capacidad del lugar ({lugar.capacidad_total})."
            })
        return data


# --- SERIALIZERS PARA EL FEED (MÓVIL) ---

class EventoFeedSerializer(serializers.ModelSerializer):
    lugar_nombre = serializers.CharField(source='lugar.nombre', read_only=True)
    promotor_razon = serializers.CharField(source='promotor.razon_social', read_only=True)
    presentaciones = PresentacionFeedSerializer(many=True, read_only=True)

    class Meta:
        model = Evento
        fields = (
            'id', 'nombre', 'estado',
            'lugar', 'lugar_nombre',
            'promotor', 'promotor_razon',
            'presentaciones',
            'fecha_inicio', 'fecha_fin',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
