from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from core.mixins import SoftDeleteMixin
from ..models import Artista, Promotor, Verificador, SeguidorPromotor
from ..serializers import (
    ArtistaSerializer, PromotorSerializer,
    VerificadorSerializer, VerificadorCrearSerializer,
)


class ArtistaViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    queryset = Artista.objects.all()
    serializer_class = ArtistaSerializer
    permission_classes = [permissions.IsAuthenticated]


class PromotorViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    queryset = Promotor.objects.all()
    serializer_class = PromotorSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='seguir')
    def seguir(self, request, pk=None):
        promotor = self.get_object()
        usuario = request.user

        seguimiento = SeguidorPromotor.objects.filter(usuario=usuario, promotor=promotor)
        if seguimiento.exists():
            seguimiento.delete()
            siguiendo = False
        else:
            SeguidorPromotor.objects.create(usuario=usuario, promotor=promotor)
            siguiendo = True

        return Response({'siguiendo': siguiendo}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='siguiendo')
    def siguiendo(self, request):
        ids = list(SeguidorPromotor.objects.filter(usuario=request.user).values_list('promotor_id', flat=True))
        return Response({'promotores_seguidos': ids}, status=status.HTTP_200_OK)


class VerificadorViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    """
    CRUD de Verificadores (creados por promotores).
    GET    /api/usuarios/verificadores/          → Listar
    POST   /api/usuarios/verificadores/          → Crear
    GET    /api/usuarios/verificadores/{id}/     → Detalle
    PUT    /api/usuarios/verificadores/{id}/     → Actualizar
    PATCH  /api/usuarios/verificadores/{id}/     → Actualizar parcial
    DELETE /api/usuarios/verificadores/{id}/     → Soft delete
    """
    queryset = Verificador.objects.select_related('usuario', 'promotor').all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser:
            return qs
        if hasattr(user, 'perfil_promotor'):
            return qs.filter(promotor=user.perfil_promotor)
        return qs.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return VerificadorCrearSerializer
        return VerificadorSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.usuario:
            instance.usuario.delete()
        instance.delete()
        return Response(
            {'detail': 'Verificador eliminado correctamente (soft delete).'},
            status=status.HTTP_200_OK
        )
