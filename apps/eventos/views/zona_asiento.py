from rest_framework import viewsets, permissions

from ..models import Zona, Asiento
from ..serializers import ZonaSerializer, AsientoSerializer
from .mixins import SoftDeleteMixin


class ZonaViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    """
    GET    /api/eventos/zonas/         → Listar (filtrable por ?evento=<id>)
    POST   /api/eventos/zonas/         → Crear
    GET    /api/eventos/zonas/{id}/    → Detalle
    PUT    /api/eventos/zonas/{id}/    → Actualizar
    PATCH  /api/eventos/zonas/{id}/    → Actualizar parcial
    DELETE /api/eventos/zonas/{id}/    → Soft delete
    """
    queryset = Zona.objects.all()
    serializer_class = ZonaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        evento_id = self.request.query_params.get('evento')
        if evento_id:
            qs = qs.filter(evento_id=evento_id)
        return qs


class AsientoViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    """
    GET    /api/eventos/asientos/         → Listar (filtrable por ?zona=<id>)
    POST   /api/eventos/asientos/         → Crear
    GET    /api/eventos/asientos/{id}/    → Detalle
    PUT    /api/eventos/asientos/{id}/    → Actualizar
    PATCH  /api/eventos/asientos/{id}/    → Actualizar parcial
    DELETE /api/eventos/asientos/{id}/    → Soft delete
    """
    queryset = Asiento.objects.all()
    serializer_class = AsientoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        zona_id = self.request.query_params.get('zona')
        if zona_id:
            qs = qs.filter(zona_id=zona_id)
        return qs
