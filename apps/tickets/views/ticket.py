from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q

from ..models import Ticket, TransferenciaTicket
from ..serializers import TicketSerializer, MisTicketsSerializer
from ..serializers.transferencia import TransferirTicketSerializer
from ..serializers.verificar import VerificarQrSerializer
from usuarios.models import Notificacion
from eventos.models import VerificadorEvento, RegistroAcceso
from .mixins import SoftDeleteMixin

Usuario = get_user_model()


class TicketViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related('zona__evento', 'factura', 'asiento').all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        factura_id = self.request.query_params.get('factura')
        zona_id = self.request.query_params.get('zona')
        if factura_id:
            qs = qs.filter(factura_id=factura_id)
        if zona_id:
            qs = qs.filter(zona_id=zona_id)
        return qs

    @action(detail=False, url_path='mis-tickets', methods=['get'])
    def mis_tickets(self, request):
        filtro = request.query_params.get('filtro', 'comprados')
        tickets = Ticket.objects.filter(
            Q(propietario=request.user)
            | Q(propietario__isnull=True, factura__cliente=request.user)
        ).select_related(
            'zona__evento', 'asiento'
        )

        if filtro == 'usados':
            tickets = tickets.filter(estado='usado')
        else:
            tickets = tickets.filter(estado='activo')

        tickets = tickets.order_by('-created_at')
        serializer = MisTicketsSerializer(tickets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='verificar-qr')
    @transaction.atomic
    def verificar_qr(self, request):
        """
        POST /api/tickets/tickets/verificar-qr/
        Body: { "codigo_qr": "MT-..." }
        """
        serializer = VerificarQrSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        codigo_qr = serializer.validated_data['codigo_qr']

        if not hasattr(request.user, 'perfil_verificador'):
            return Response(
                {'detail': 'Solo los verificadores pueden escanear tickets.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        verificador = request.user.perfil_verificador
        if verificador.estado != 'activo':
            return Response(
                {'detail': 'Tu perfil de verificador no está activo.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            ticket = Ticket.objects.select_related(
                'zona__evento__promotor'
            ).get(codigo_qr=codigo_qr)
        except Ticket.DoesNotExist:
            return Response(
                {'detail': 'Ticket no encontrado. Código QR inválido.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        evento = ticket.zona.evento
        verificador_evento, _ = VerificadorEvento.objects.get_or_create(
            evento=evento,
            verificador=verificador,
        )

        if evento.promotor_id != verificador.promotor_id:
            RegistroAcceso.objects.create(
                verificador_evento=verificador_evento,
                ticket=ticket,
                resultado='invalido',
            )
            return Response(
                {'detail': 'Este ticket no pertenece a un evento de tu promotor.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if ticket.estado == 'usado':
            RegistroAcceso.objects.create(
                verificador_evento=verificador_evento,
                ticket=ticket,
                resultado='ya_usado',
            )
            return Response(
                {'detail': 'Este ticket ya fue utilizado anteriormente.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if ticket.estado != 'activo':
            RegistroAcceso.objects.create(
                verificador_evento=verificador_evento,
                ticket=ticket,
                resultado='invalido',
            )
            return Response(
                {'detail': f'Ticket con estado "{ticket.estado}". No se puede validar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ticket.estado = 'usado'
        ticket.save(update_fields=['estado', 'updated_at'])

        RegistroAcceso.objects.create(
            verificador_evento=verificador_evento,
            ticket=ticket,
            resultado='aprobado',
        )

        return Response(
            {
                'detail': 'Ticket verificado correctamente. Acceso aprobado.',
                'ticket': MisTicketsSerializer(ticket).data,
                'evento_nombre': evento.nombre,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='transferir')
    @transaction.atomic
    def transferir(self, request, pk=None):
        ticket = self.get_object()
        serializer = TransferirTicketSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        destinatario = Usuario.objects.get(id=serializer.validated_data['destinatario_id'])

        if ticket.propietario_id != request.user.id and not (
            ticket.propietario_id is None and ticket.factura.cliente_id == request.user.id
        ):
            return Response(
                {'detail': 'Solo el propietario actual puede transferir este ticket.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if ticket.transferido:
            return Response(
                {'detail': 'Este ticket ya fue transferido anteriormente. Solo se permite una transferencia.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if ticket.estado != 'activo':
            return Response(
                {'detail': f'No se puede transferir un ticket con estado "{ticket.estado}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        evento = ticket.zona.evento
        if evento.fecha_inicio <= timezone.now():
            return Response(
                {'detail': 'No se puede transferir un ticket de un evento que ya comenzó.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not destinatario.has_role('fan'):
            return Response(
                {'detail': 'Solo puedes transferir tickets a usuarios con rol fan.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        TransferenciaTicket.objects.create(
            ticket=ticket,
            origen=request.user,
            destino=destinatario,
        )

        ticket.propietario = destinatario
        ticket.transferido = True
        ticket.save(update_fields=['propietario', 'transferido', 'updated_at'])

        Notificacion.objects.create(
            usuario=destinatario,
            titulo='¡Recibiste un ticket!',
            mensaje=(
                f'{request.user.username} te transfirió un ticket para '
                f'"{evento.nombre}" ({ticket.zona.nombre}).'
            ),
            tipo='ticket_recibido',
            evento=evento,
        )

        return Response(
            {
                'detail': f'Ticket transferido exitosamente a {destinatario.username}.',
                'ticket': MisTicketsSerializer(ticket).data,
            },
            status=status.HTTP_200_OK,
        )
