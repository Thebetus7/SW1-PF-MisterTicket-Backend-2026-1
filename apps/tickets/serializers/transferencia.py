from rest_framework import serializers


class TransferirTicketSerializer(serializers.Serializer):
    destinatario_id = serializers.IntegerField()

    def validate_destinatario_id(self, value):
        from django.contrib.auth import get_user_model
        Usuario = get_user_model()
        request = self.context['request']
        if value == request.user.id:
            raise serializers.ValidationError('No puedes transferir un ticket a ti mismo.')
        if not Usuario.objects.filter(id=value).exists():
            raise serializers.ValidationError('El usuario destinatario no existe.')
        return value
