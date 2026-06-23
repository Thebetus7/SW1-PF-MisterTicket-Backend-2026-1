from rest_framework import serializers
from ..models import PresentacionEvento


class PresentacionEventoSerializer(serializers.ModelSerializer):
    artista_nombre = serializers.CharField(
        source='artista.nombre_artistico', read_only=True
    )
    artista_biografia = serializers.CharField(
        source='artista.biografia', read_only=True
    )
    artista_popularidad = serializers.IntegerField(
        source='artista.popularidad', read_only=True
    )
    artista_departamento_origen = serializers.CharField(
        source='artista.departamento_origen.nombre', read_only=True, default=None
    )
    artista_generos = serializers.SerializerMethodField()
    evento_nombre = serializers.CharField(source='evento.nombre', read_only=True)

    class Meta:
        model = PresentacionEvento
        fields = (
            'id', 'orden_aparicion', 'tiempo_inicio',
            'evento', 'evento_nombre',
            'artista', 'artista_nombre',
            'artista_biografia', 'artista_popularidad',
            'artista_departamento_origen', 'artista_generos',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_artista_generos(self, obj):
        if obj.artista:
            return [g.nombre for g in obj.artista.generos_musicales.all()]
        return []
