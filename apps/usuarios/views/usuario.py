from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django.contrib.auth import get_user_model
from core.mixins import SoftDeleteMixin

from ..serializers import UsuarioSerializer, UsuarioRegistroSerializer

Usuario = get_user_model()


class UsuarioViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    """
    CRUD completo de Usuarios.
    GET    /api/usuarios/usuarios/       → Listar todos
    POST   /api/usuarios/usuarios/       → Crear (usa serializer de registro)
    GET    /api/usuarios/usuarios/{id}/  → Detalle
    PUT    /api/usuarios/usuarios/{id}/  → Actualizar
    PATCH  /api/usuarios/usuarios/{id}/  → Actualizar parcial
    DELETE /api/usuarios/usuarios/{id}/  → Soft delete
    GET    /api/usuarios/usuarios/{id}/roles/ → Ver roles del usuario
    """
    queryset = Usuario.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['username', 'email']

    def get_serializer_class(self):
        """Usa serializer de registro para crear y de lectura para el resto."""
        if self.action == 'create':
            return UsuarioRegistroSerializer
        return UsuarioSerializer

    @action(detail=True, methods=['get'], url_path='roles')
    def roles(self, request, pk=None):
        """GET /api/usuarios/usuarios/{id}/roles/ → Lista los roles del usuario."""
        usuario = self.get_object()
        return Response({'roles': usuario.get_roles()})

    @action(detail=True, methods=['post'], url_path='asignar-rol')
    def asignar_rol(self, request, pk=None):
        """
        POST /api/usuarios/usuarios/{id}/asignar-rol/
        Body: {"rol": "organizador"}
        Asigna un rol al usuario.
        """
        from django.contrib.auth.models import Group
        usuario = self.get_object()
        rol_nombre = request.data.get('rol')
        if not rol_nombre:
            return Response({'error': 'El campo "rol" es requerido.'}, status=400)
        try:
            grupo = Group.objects.get(name=rol_nombre)
            usuario.groups.add(grupo)
            return Response({'detail': f'Rol "{rol_nombre}" asignado correctamente.'})
        except Group.DoesNotExist:
            return Response({'error': f'El rol "{rol_nombre}" no existe.'}, status=404)

    @action(detail=False, methods=['get'], url_path='fans')
    def fans(self, request):
        """
        GET /api/usuarios/lista/fans/
        Lista todos los usuarios con rol fan (excluye al usuario autenticado).
        Para transferencia rápida en demo/examen.
        """
        fans = Usuario.objects.filter(
            groups__name='fan',
            is_active=True,
        ).exclude(
            id=request.user.id
        ).distinct().order_by('username')

        data = [{'id': u.id, 'username': u.username} for u in fans]
        return Response(data, status=status.HTTP_200_OK)
