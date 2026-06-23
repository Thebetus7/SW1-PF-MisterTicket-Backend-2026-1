from rest_framework import serializers
from ..models import VerificadorEvento, RegistroAcceso


class VerificadorEventoSerializer(serializers.ModelSerializer):
    verificador_username = serializers.CharField(
        source='verificador.usuario.username', read_only=True
    )
    evento_nombre = serializers.CharField(source='evento.nombre', read_only=True)

    class Meta:
        model = VerificadorEvento
        fields = (
            'id',
            'evento', 'evento_nombre',
            'verificador', 'verificador_username',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class RegistroAccesoSerializer(serializers.ModelSerializer):
    verificador_evento_id = serializers.IntegerField(
        source='verificador_evento.id', read_only=True
    )

    class Meta:
        model = RegistroAcceso
        fields = (
            'id', 'resultado',
            'verificador_evento', 'verificador_evento_id',
            'ticket',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class MisRegistroAccesoSerializer(serializers.ModelSerializer):
    evento_nombre = serializers.SerializerMethodField()
    ticket_codigo_qr = serializers.CharField(source='ticket.codigo_qr', read_only=True)
    zona_nombre = serializers.CharField(source='ticket.zona.nombre', read_only=True)

    class Meta:
        model = RegistroAcceso
        fields = (
            'id', 'resultado', 'ticket_codigo_qr',
            'evento_nombre', 'zona_nombre', 'created_at',
        )

    def get_evento_nombre(self, obj):
        if obj.verificador_evento and obj.verificador_evento.evento:
            return obj.verificador_evento.evento.nombre
        if obj.ticket and obj.ticket.zona and obj.ticket.zona.evento:
            return obj.ticket.zona.evento.nombre
        return ''
