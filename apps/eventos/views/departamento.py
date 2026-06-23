from rest_framework import viewsets, permissions

from ..models import Departamento
from ..serializers import DepartamentoSerializer
from .mixins import SoftDeleteMixin


class DepartamentoViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    """
    GET    /api/eventos/departamentos/         → Listar
    POST   /api/eventos/departamentos/         → Crear
    GET    /api/eventos/departamentos/{id}/    → Detalle
    PUT    /api/eventos/departamentos/{id}/    → Actualizar
    PATCH  /api/eventos/departamentos/{id}/    → Actualizar parcial
    DELETE /api/eventos/departamentos/{id}/    → Soft delete
    """
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer
    permission_classes = [permissions.IsAuthenticated]
