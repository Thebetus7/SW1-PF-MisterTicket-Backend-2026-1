from rest_framework import serializers
from ..models import Artista, Promotor, Verificador
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

Usuario = get_user_model()


class ArtistaSerializer(serializers.ModelSerializer):
    foto_url = serializers.ReadOnlyField()
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    departamento_origen_nombre = serializers.CharField(source='departamento_origen.nombre', read_only=True)
    generos_musicales_nombres = serializers.SerializerMethodField()

    class Meta:
        model = Artista
        fields = (
            'id', 'nombre_artistico', 'biografia',
            'foto', 'foto_url',
            'usuario', 'usuario_username',
            'generos_musicales', 'generos_musicales_nombres',
            'departamento_origen', 'departamento_origen_nombre',
            'popularidad',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'foto_url', 'created_at', 'updated_at')

    def get_generos_musicales_nombres(self, obj):
        return [g.nombre for g in obj.generos_musicales.all()]


class PromotorSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Promotor
        fields = (
            'id', 'razon_social', 'nit_rfc',
            'banco_nombre', 'cuenta_bancaria',
            'usuario', 'usuario_username',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class VerificadorSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    usuario_email = serializers.EmailField(source='usuario.email', read_only=True)
    usuario_first_name = serializers.CharField(source='usuario.first_name', read_only=True)
    usuario_last_name = serializers.CharField(source='usuario.last_name', read_only=True)
    promotor_razon = serializers.CharField(source='promotor.razon_social', read_only=True)

    class Meta:
        model = Verificador
        fields = (
            'id', 'pago', 'estado',
            'usuario', 'usuario_username', 'usuario_email',
            'usuario_first_name', 'usuario_last_name',
            'promotor', 'promotor_razon',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'usuario')


class VerificadorCrearSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    promotor = serializers.PrimaryKeyRelatedField(queryset=Promotor.objects.all(), required=False, allow_null=True)
    estado = serializers.CharField(max_length=50, default='activo')
    pago = serializers.DecimalField(max_digits=10, decimal_places=2, default=0, required=False)

    def validate_username(self, value):
        if Usuario.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        return value

    def validate_email(self, value):
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo electrónico ya está en uso.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')
        promotor = validated_data.pop('promotor', None)
        estado = validated_data.get('estado', 'activo')
        pago = validated_data.get('pago', 0)

        if not promotor and 'request' in self.context:
            user = self.context['request'].user
            if hasattr(user, 'perfil_promotor'):
                promotor = user.perfil_promotor

        if not promotor:
            raise serializers.ValidationError({"promotor": "Se requiere un promotor válido para crear un verificador."})

        usuario = Usuario.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        try:
            grupo = Group.objects.get(name='verificador')
            usuario.groups.add(grupo)
        except Group.DoesNotExist:
            pass

        verificador = Verificador.objects.create(
            usuario=usuario,
            promotor=promotor,
            estado=estado,
            pago=pago,
        )

        return verificador
