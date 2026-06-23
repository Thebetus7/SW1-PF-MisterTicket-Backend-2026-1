from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import Notificacion, DispositivoUsuario
from ..serializers import NotificacionSerializer


class NotificacionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para ver, marcar como leídas y eliminar notificaciones del usuario actual.
    GET    /api/usuarios/notificaciones/       → Listar notificaciones del usuario logueado.
    DELETE /api/usuarios/notificaciones/{id}/  → Eliminar físicamente una notificación (deslizar).
    """
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Solo mostrar notificaciones pertenecientes al usuario logueado
        return Notificacion.objects.filter(usuario=self.request.user)

    @action(detail=True, methods=['patch'], url_path='leer')
    def leer(self, request, pk=None):
        """
        PATCH /api/usuarios/notificaciones/{id}/leer/
        Marca una notificación como leída.
        """
        notificacion = self.get_object()
        notificacion.leido = True
        notificacion.save()
        return Response({'status': 'Notificación marcada como leída'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='leer-todas')
    def leer_todas(self, request):
        """
        POST /api/usuarios/notificaciones/leer-todas/
        Marca todas las notificaciones del usuario actual como leídas.
        """
        self.get_queryset().filter(leido=False).update(leido=True)
        return Response({'status': 'Todas las notificaciones marcadas como leídas'}, status=status.HTTP_200_OK)


class DispositivoViewSet(viewsets.ViewSet):
    """
    Endpoints para registrar y desvincular tokens FCM de dispositivos móviles.
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='registrar')
    def registrar(self, request):
        """
        POST /api/usuarios/dispositivos/registrar/
        Body: {"fcm_token": "..."}
        Registra el token FCM en la base de datos asociado al usuario logueado.
        """
        fcm_token = request.data.get('fcm_token')
        if not fcm_token:
            return Response({'error': 'El campo fcm_token es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        # Usamos update_or_create para evitar duplicados del mismo token y asociarlo al usuario actual
        dispositivo, created = DispositivoUsuario.objects.update_or_create(
            fcm_token=fcm_token,
            defaults={'usuario': request.user}
        )

        return Response({
            'detail': 'Dispositivo registrado correctamente.',
            'created': created
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
