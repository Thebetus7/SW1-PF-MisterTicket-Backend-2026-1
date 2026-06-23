from rest_framework import serializers
from ..models import Notificacion
from eventos.serializers.evento import EventoSerializer


class NotificacionSerializer(serializers.ModelSerializer):
    evento_nombre = serializers.CharField(source='evento.nombre', read_only=True)
    evento_id = serializers.IntegerField(source='evento.id', read_only=True)
    
    class Meta:
        model = Notificacion
        fields = (
            'id', 'titulo', 'mensaje', 'tipo', 
            'leido', 'evento_id', 'evento_nombre', 'created_at'
        )
        read_only_fields = ('id', 'created_at', 'evento_nombre', 'evento_id')
