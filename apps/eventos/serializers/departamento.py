from rest_framework import serializers
from ..models import Departamento


class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = ('id', 'nombre', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
