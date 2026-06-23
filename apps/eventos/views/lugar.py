from rest_framework import viewsets, permissions

from ..models import Lugar
from ..serializers import LugarSerializer
from .mixins import SoftDeleteMixin


class LugarViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    """
    GET    /api/eventos/lugares/         → Listar
    POST   /api/eventos/lugares/         → Crear
    GET    /api/eventos/lugares/{id}/    → Detalle
    PUT    /api/eventos/lugares/{id}/    → Actualizar
    PATCH  /api/eventos/lugares/{id}/    → Actualizar parcial
    DELETE /api/eventos/lugares/{id}/    → Soft delete
    """
    queryset = Lugar.objects.all()
    serializer_class = LugarSerializer
    permission_classes = [permissions.IsAuthenticated]
