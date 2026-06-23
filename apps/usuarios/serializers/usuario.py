from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from ..models import Artista, Promotor, Verificador
from .persona import PersonaSerializer

Usuario = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    persona = PersonaSerializer(read_only=True)
    foto_url = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = (
            'id', 'username', 'email',
            'first_name', 'last_name',
            'persona', 'roles',
            'foto', 'foto_url',
            'is_active', 'is_superuser', 'is_staff', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'roles', 'is_superuser', 'is_staff')

    def get_roles(self, obj):
        return obj.get_roles()

    def get_foto_url(self, obj):
        if obj.foto:
            url = obj.foto.url
            if url.startswith(('http://', 'https://')):
                return url
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(url)
            return url
        return None


class UsuarioRegistroSerializer(serializers.ModelSerializer):
    """
    Serializer para crear usuarios nuevos.
    Acepta password en texto plano y lo hashea automáticamente.
    Se puede pasar rol_nombre para asignarlo al usuario (ej: 'promotor').
    """
    password = serializers.CharField(write_only=True, min_length=6)
    rol_nombre = serializers.ChoiceField(
        choices=['promotor', 'verificador', 'artista'],
        write_only=True, required=False, allow_blank=True, allow_null=True
    )

    class Meta:
        model = Usuario
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name', 'rol_nombre')
        read_only_fields = ('id',)

    def create(self, validated_data):
        rol_nombre = validated_data.pop('rol_nombre', None)
        password = validated_data.pop('password')
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()

        # Asignar rol si se especificó
        if rol_nombre:
            try:
                grupo = Group.objects.get(name=rol_nombre)
                usuario.groups.add(grupo)

                # Crear el perfil correspondiente automáticamente
                if rol_nombre == 'promotor':
                    Promotor.objects.create(
                        usuario=usuario,
                        razon_social=f"Promotor {usuario.first_name} {usuario.last_name}".strip() or usuario.username,
                        nit_rfc="000000",
                        banco_nombre="Pendiente",
                        cuenta_bancaria="Pendiente"
                    )
                elif rol_nombre == 'artista':
                    Artista.objects.create(
                        usuario=usuario,
                        nombre_artistico=f"{usuario.first_name} {usuario.last_name}".strip() or usuario.username
                    )
                elif rol_nombre == 'verificador':
                    Verificador.objects.create(
                        usuario=usuario,
                        pago=0.0
                    )
            except Group.DoesNotExist:
                pass

        return usuario


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extiende el login JWT para incluir los datos del usuario logueado.
    La respuesta incluye: access, refresh, usuario{}
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        data['usuario'] = UsuarioSerializer(
            self.user,
            context={'request': self.context.get('request')}
        ).data
        return data


class PerfilSerializer(serializers.ModelSerializer):
    """
    Serializer para ver y actualizar el perfil del usuario autenticado.
    Soporta actualización anidada de Persona y Artista.
    Compatible con multipart/form-data para subir la foto de perfil.

    Campos de solo lectura extra:
      - roles, foto_url, nombre_artistico, biografia

    Campos editables de Persona (anidados):
      - nombre_completo (source: persona.nombre)
      - ci (source: persona.ci)

    Campos editables de Artista (write_only, solo si el usuario es artista):
      - nombre_artistico_update
      - biografia_update
    """
    roles = serializers.SerializerMethodField(read_only=True)
    foto_url = serializers.SerializerMethodField(read_only=True)

    # Datos de Persona (editables, mapeados al objeto persona relacionado)
    nombre_completo = serializers.CharField(
        source='persona.nombre', required=False, allow_blank=True,
        help_text='Nombre completo (de la tabla Persona)'
    )
    ci = serializers.CharField(
        source='persona.ci', required=False, allow_blank=True,
        help_text='Cédula de identidad (de la tabla Persona)'
    )

    # Datos de Artista — lectura
    nombre_artistico = serializers.SerializerMethodField(read_only=True)
    biografia = serializers.SerializerMethodField(read_only=True)

    # Datos de Artista — escritura
    nombre_artistico_update = serializers.CharField(
        write_only=True, required=False, allow_blank=True,
        help_text='Nombre artístico (solo para artistas)'
    )
    biografia_update = serializers.CharField(
        write_only=True, required=False, allow_blank=True,
        help_text='Biografía (solo para artistas)'
    )

    class Meta:
        model = Usuario
        fields = (
            'id', 'username', 'email',
            'first_name', 'last_name',
            'foto', 'foto_url',
            'roles',
            # Persona
            'nombre_completo', 'ci',
            # Artista
            'nombre_artistico', 'biografia',
            'nombre_artistico_update', 'biografia_update',
            'recibir_notificaciones',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'username', 'created_at', 'updated_at', 'roles')
        extra_kwargs = {
            'foto': {'required': False},
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def get_roles(self, obj):
        return obj.get_roles()

    def get_foto_url(self, obj):
        if obj.foto:
            try:
                url = obj.foto.url
                if url.startswith(('http://', 'https://')):
                    return url
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(url)
                return url
            except Exception:
                return None
        return None

    def get_nombre_artistico(self, obj):
        try:
            if obj.perfil_artista:
                return obj.perfil_artista.nombre_artistico
        except Exception:
            pass
        return None

    def get_biografia(self, obj):
        try:
            if obj.perfil_artista:
                return obj.perfil_artista.biografia
        except Exception:
            pass
        return None

    def update(self, instance, validated_data):
        # ─── Extraer datos anidados antes de actualizar ───
        persona_data = validated_data.pop('persona', {})
        nombre_artistico = validated_data.pop('nombre_artistico_update', None)
        biografia = validated_data.pop('biografia_update', None)

        # ─── Actualizar campos del modelo Usuario ───
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # ─── Actualizar Persona si hay datos ───
        if persona_data and instance.persona:
            for attr, value in persona_data.items():
                setattr(instance.persona, attr, value)
            instance.persona.save()

        # ─── Actualizar Artista si el usuario tiene ese perfil ───
        if nombre_artistico is not None or biografia is not None:
            try:
                artista = instance.perfil_artista
                if nombre_artistico is not None:
                    artista.nombre_artistico = nombre_artistico
                if biografia is not None:
                    artista.biografia = biografia
                artista.save()
            except Exception:
                pass

        return instance
