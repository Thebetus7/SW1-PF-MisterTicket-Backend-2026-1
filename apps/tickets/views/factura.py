from rest_framework import viewsets, permissions

from ..models import Factura
from ..serializers import FacturaSerializer
from .mixins import SoftDeleteMixin


class FacturaViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    """
    GET    /api/tickets/facturas/         → Listar (filtrable por ?cliente=<id>)
    POST   /api/tickets/facturas/         → Crear
    GET    /api/tickets/facturas/{id}/    → Detalle
    PUT    /api/tickets/facturas/{id}/    → Actualizar
    PATCH  /api/tickets/facturas/{id}/    → Actualizar parcial (ej: estado_pago)
    DELETE /api/tickets/facturas/{id}/    → Soft delete
    """
    queryset = Factura.objects.select_related('cliente').all()
    serializer_class = FacturaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        cliente_id = self.request.query_params.get('cliente')
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)
        # El usuario solo ve sus propias facturas a menos que sea admin
        if not self.request.user.is_staff:
            qs = qs.filter(cliente=self.request.user)
        return qs
