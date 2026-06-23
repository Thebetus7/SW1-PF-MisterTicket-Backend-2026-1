from rest_framework import viewsets, permissions

from ..models import PresentacionEvento
from ..serializers import PresentacionEventoSerializer
from .mixins import SoftDeleteMixin


class PresentacionEventoViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    """
    GET    /api/eventos/presentaciones/         → Listar (filtrable por ?evento=<id>)
    POST   /api/eventos/presentaciones/         → Crear
    GET    /api/eventos/presentaciones/{id}/    → Detalle
    PUT    /api/eventos/presentaciones/{id}/    → Actualizar
    PATCH  /api/eventos/presentaciones/{id}/    → Actualizar parcial
    DELETE /api/eventos/presentaciones/{id}/    → Soft delete
    """
    queryset = PresentacionEvento.objects.select_related('evento', 'artista').all()
    serializer_class = PresentacionEventoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        evento_id = self.request.query_params.get('evento')
        if evento_id:
            qs = qs.filter(evento_id=evento_id)
        return qs
