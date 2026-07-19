from rest_framework import serializers
from ..models import Cancion

class CancionSerializer(serializers.ModelSerializer):
    archivo_url = serializers.ReadOnlyField()
    artista_nombre = serializers.CharField(source='artista.nombre_artistico', read_only=True)
    duracion_formateada = serializers.SerializerMethodField(read_only=True)
    tamano_formateado = serializers.SerializerMethodField(read_only=True)
    plagio_de_titulo = serializers.CharField(source='plagio_de.nombre', read_only=True, default=None)

    class Meta:
        model = Cancion
        fields = (
            'id', 'nombre', 'detalle', 'archivo', 'archivo_url',
            'artista', 'artista_nombre', 'publicado',
            'duracion', 'duracion_formateada',
            'tamano', 'tamano_formateado',
            'formato',
            'bpm', 'genero_ia', 'energia_ia', 'brillo_ia',
            'es_plagio', 'similitud_plagio', 'plagio_de', 'plagio_de_titulo',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'artista', 'archivo_url', 'duracion', 'tamano', 'formato', 
            'bpm', 'genero_ia', 'energia_ia', 'brillo_ia', 
            'es_plagio', 'similitud_plagio', 'plagio_de', 'plagio_de_titulo', 
            'created_at', 'updated_at'
        )

    def get_duracion_formateada(self, obj):
        if obj.duracion:
            minutos = int(obj.duracion // 60)
            segundos = int(obj.duracion % 60)
            return f"{minutos}:{segundos:02d}"
        return "0:00"

    def get_tamano_formateado(self, obj):
        if obj.tamano:
            kb = obj.tamano / 1024
            if kb > 1024:
                mb = kb / 1024
                return f"{mb:.2f} MB"
            return f"{kb:.1f} KB"
        return "0 KB"
