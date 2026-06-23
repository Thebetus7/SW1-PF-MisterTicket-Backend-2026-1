from rest_framework import serializers


class VerificarQrSerializer(serializers.Serializer):
    codigo_qr = serializers.CharField(max_length=255)
