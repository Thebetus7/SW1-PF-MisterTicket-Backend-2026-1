from rest_framework import serializers
from ..models import Amistad


class AmistadSerializer(serializers.ModelSerializer):
    solicitante_username = serializers.CharField(source='solicitante.username', read_only=True)
    receptor_username = serializers.CharField(source='receptor.username', read_only=True)

    class Meta:
        model = Amistad
        fields = (
            'id', 'solicitante', 'solicitante_username',
            'receptor', 'receptor_username',
            'estado', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'estado', 'created_at', 'updated_at')


class AmigoSerializer(serializers.Serializer):
    """Representación simplificada de un amigo aceptado."""
    id = serializers.IntegerField()
    username = serializers.CharField()
    amistad_id = serializers.IntegerField()


class SolicitudAmistadSerializer(serializers.Serializer):
    usuario_id = serializers.IntegerField()

    def validate_usuario_id(self, value):
        from django.contrib.auth import get_user_model
        Usuario = get_user_model()
        request = self.context['request']
        if value == request.user.id:
            raise serializers.ValidationError('No puedes enviarte una solicitud a ti mismo.')
        if not Usuario.objects.filter(id=value).exists():
            raise serializers.ValidationError('El usuario no existe.')
        return value
