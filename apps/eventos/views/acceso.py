from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import VerificadorEvento, RegistroAcceso
from ..serializers import VerificadorEventoSerializer, RegistroAccesoSerializer, MisRegistroAccesoSerializer
from .mixins import SoftDeleteMixin


class VerificadorEventoViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    queryset = VerificadorEvento.objects.select_related('evento', 'verificador').all()
    serializer_class = VerificadorEventoSerializer
    permission_classes = [permissions.IsAuthenticated]


class RegistroAccesoViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    queryset = RegistroAcceso.objects.all()
    serializer_class = RegistroAccesoSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        ticket_id = self.request.query_params.get('ticket')
        if ticket_id:
            qs = qs.filter(ticket_id=ticket_id)
        return qs

    @action(detail=False, methods=['get'], url_path='mis-registros')
    def mis_registros(self, request):
        """
        GET /api/eventos/registros-acceso/mis-registros/
        Lista los últimos escaneos del verificador autenticado.
        """
        if not hasattr(request.user, 'perfil_verificador'):
            return Response(
                {'detail': 'Solo los verificadores pueden ver su historial de escaneos.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        verificador = request.user.perfil_verificador
        registros = RegistroAcceso.objects.filter(
            verificador_evento__verificador=verificador
        ).select_related(
            'ticket__zona__evento',
            'verificador_evento__evento',
        ).order_by('-created_at')[:50]

        serializer = MisRegistroAccesoSerializer(registros, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
