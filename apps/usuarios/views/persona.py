from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from core.mixins import SoftDeleteMixin

from ..models import Persona
from ..serializers import PersonaSerializer


class PersonaViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    """
    CRUD completo de Personas.
    GET    /api/personas/          → Listar todas
    POST   /api/personas/          → Crear
    GET    /api/personas/{id}/     → Detalle
    PUT    /api/personas/{id}/     → Actualizar completo
    PATCH  /api/personas/{id}/     → Actualizar parcial
    DELETE /api/personas/{id}/     → Soft delete
    """
    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer
    permission_classes = [permissions.IsAuthenticated]
