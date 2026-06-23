from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth import get_user_model

from ..models import Amistad
from ..serializers.amistad import AmistadSerializer, AmigoSerializer, SolicitudAmistadSerializer

Usuario = get_user_model()


class AmistadViewSet(viewsets.GenericViewSet):
    """
    Gestión de amistades entre usuarios fan.

    POST   /api/usuarios/amistades/solicitar/          → Enviar solicitud
    GET    /api/usuarios/amistades/mis-amigos/         → Listar amigos aceptados
    GET    /api/usuarios/amistades/solicitudes/         → Solicitudes pendientes recibidas
    POST   /api/usuarios/amistades/{id}/aceptar/       → Aceptar solicitud
    POST   /api/usuarios/amistades/{id}/rechazar/      → Rechazar solicitud
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Amistad.objects.all()
    serializer_class = AmistadSerializer

    @action(detail=False, methods=['post'], url_path='solicitar')
    def solicitar(self, request):
        serializer = SolicitudAmistadSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        receptor = Usuario.objects.get(id=serializer.validated_data['usuario_id'])

        existente = Amistad.objects.filter(
            Q(solicitante=request.user, receptor=receptor)
            | Q(solicitante=receptor, receptor=request.user)
        ).first()

        if existente:
            if existente.estado == 'aceptada':
                return Response({'detail': 'Ya son amigos.'}, status=status.HTTP_400_BAD_REQUEST)
            if existente.estado == 'pendiente':
                return Response({'detail': 'Ya existe una solicitud pendiente.'}, status=status.HTTP_400_BAD_REQUEST)
            if existente.estado == 'rechazada':
                existente.solicitante = request.user
                existente.receptor = receptor
                existente.estado = 'pendiente'
                existente.save()
                amistad = existente
            else:
                amistad = existente
        else:
            amistad = Amistad.objects.create(
                solicitante=request.user,
                receptor=receptor,
                estado='pendiente',
            )

        from ..models import Notificacion
        Notificacion.objects.create(
            usuario=receptor,
            titulo='Nueva solicitud de amistad',
            mensaje=f'{request.user.username} quiere ser tu amigo en MisterTicket.',
            tipo='solicitud_amistad',
        )

        return Response(AmistadSerializer(amistad).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='mis-amigos')
    def mis_amigos(self, request):
        amistades = Amistad.objects.filter(
            Q(solicitante=request.user) | Q(receptor=request.user),
            estado='aceptada',
        ).select_related('solicitante', 'receptor')

        amigos = []
        for amistad in amistades:
            amigo = amistad.get_amigo(request.user)
            amigos.append({
                'id': amigo.id,
                'username': amigo.username,
                'amistad_id': amistad.id,
            })

        return Response(AmigoSerializer(amigos, many=True).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='solicitudes')
    def solicitudes(self, request):
        pendientes = Amistad.objects.filter(
            receptor=request.user,
            estado='pendiente',
        ).select_related('solicitante')
        serializer = AmistadSerializer(pendientes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='aceptar')
    def aceptar(self, request, pk=None):
        amistad = self.get_object()
        if amistad.receptor_id != request.user.id:
            return Response({'detail': 'Solo el receptor puede aceptar.'}, status=status.HTTP_403_FORBIDDEN)
        if amistad.estado != 'pendiente':
            return Response({'detail': 'La solicitud ya fue procesada.'}, status=status.HTTP_400_BAD_REQUEST)

        amistad.estado = 'aceptada'
        amistad.save()

        return Response(AmistadSerializer(amistad).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='rechazar')
    def rechazar(self, request, pk=None):
        amistad = self.get_object()
        if amistad.receptor_id != request.user.id:
            return Response({'detail': 'Solo el receptor puede rechazar.'}, status=status.HTTP_403_FORBIDDEN)
        if amistad.estado != 'pendiente':
            return Response({'detail': 'La solicitud ya fue procesada.'}, status=status.HTTP_400_BAD_REQUEST)

        amistad.estado = 'rechazada'
        amistad.save()

        return Response(AmistadSerializer(amistad).data, status=status.HTTP_200_OK)
