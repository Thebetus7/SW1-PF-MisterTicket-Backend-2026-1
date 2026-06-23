from rest_framework import generics, permissions, parsers
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.conf import settings
import logging

from ..serializers import (
    CustomTokenObtainPairSerializer,
    UsuarioRegistroSerializer,
    UsuarioSerializer,
    PerfilSerializer,
)

logger = logging.getLogger(__name__)
Usuario = get_user_model()


class LoginView(TokenObtainPairView):
    """
    POST /api/usuarios/login/
    Retorna access_token, refresh_token y datos del usuario con sus roles.
    """
    serializer_class = CustomTokenObtainPairSerializer


class RegistroView(generics.CreateAPIView):
    """
    POST /api/usuarios/registro/
    Crea un nuevo usuario. No requiere autenticación.
    Acepta: username, email, password, first_name, last_name, rol_nombre
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioRegistroSerializer
    permission_classes = [permissions.AllowAny]


class PerfilView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/usuarios/perfil/  -> Ver mi perfil (datos, persona, artista si aplica)
    PUT   /api/usuarios/perfil/  -> Actualizar mi perfil (incluyendo foto de perfil)
    PATCH /api/usuarios/perfil/  -> Actualizar parcialmente mi perfil

    Acepta multipart/form-data para la subida de la foto de perfil.
    """
    serializer_class = PerfilSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [
        parsers.MultiPartParser,
        parsers.FormParser,
        parsers.JSONParser,
    ]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        instance = serializer.save()
        # Log de verificacion: mostrar donde se guardo la foto
        storage_type = 'MinIO/S3' if getattr(settings, 'USE_S3', False) else 'LOCAL'
        if instance.foto:
            try:
                foto_url = instance.foto.url
                foto_storage = instance.foto.storage.__class__.__name__
                print(f'[PERFIL] Foto guardada -> Storage: {storage_type} ({foto_storage}) | URL: {foto_url}')
            except Exception as e:
                print(f'[PERFIL] Error obteniendo URL de foto -> {e}')
        else:
            print(f'[PERFIL] Perfil actualizado sin foto -> Storage configurado: {storage_type}')
