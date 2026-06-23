from rest_framework import serializers
from ..models import GeneroMusical


class GeneroMusicalSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneroMusical
        fields = ('id', 'nombre', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
