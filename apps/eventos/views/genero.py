from rest_framework import viewsets, permissions

from ..models import GeneroMusical
from ..serializers import GeneroMusicalSerializer
from .mixins import SoftDeleteMixin


class GeneroMusicalViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    """
    GET    /api/eventos/generos/         → Listar
    POST   /api/eventos/generos/         → Crear
    GET    /api/eventos/generos/{id}/    → Detalle
    PUT    /api/eventos/generos/{id}/    → Actualizar
    PATCH  /api/eventos/generos/{id}/    → Actualizar parcial
    DELETE /api/eventos/generos/{id}/    → Soft delete
    """
    queryset = GeneroMusical.objects.all()
    serializer_class = GeneroMusicalSerializer
    permission_classes = [permissions.IsAuthenticated]
