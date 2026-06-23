from rest_framework import serializers
from ..models import Persona


class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = ('id', 'nombre', 'ci', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
