from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from core.mixins import SoftDeleteMixin
from ..models import Cancion
from ..serializers import CancionSerializer

class CancionViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    """
    CRUD completo de Canciones del Artista autenticado.
    GET    /api/musica/canciones/          → Listar canciones del artista autenticado
    POST   /api/musica/canciones/          → Crear canción (subida de archivo via form-data)
    GET    /api/musica/canciones/{id}/     → Detalle de una canción
    PUT    /api/musica/canciones/{id}/     → Actualizar
    PATCH  /api/musica/canciones/{id}/     → Actualizar parcial
    DELETE /api/musica/canciones/{id}/     → Eliminar canción
    """
    serializer_class = CancionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        artista_id = self.request.query_params.get('artista_id')

        if artista_id:
            # Permite a los fans obtener las canciones públicas de un artista específico
            return Cancion.objects.filter(artista_id=artista_id, publicado=True)

        # Si el usuario no tiene perfil de artista asignado, no puede ver ni subir nada
        if not hasattr(user, 'perfil_artista') or user.perfil_artista is None:
            return Cancion.objects.none()
        return Cancion.objects.filter(artista=user.perfil_artista)

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, 'perfil_artista') or user.perfil_artista is None:
            raise ValidationError(
                {"detail": "El usuario no posee un perfil de Artista registrado para subir música."}
            )
        serializer.save(artista=user.perfil_artista)
