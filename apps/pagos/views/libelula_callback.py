import logging

from django.db import transaction
from django.db.models import F
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response

from tickets.models import Factura, Ticket

logger = logging.getLogger(__name__)


class LibelulaCallbackView(APIView):
    """
    GET /api/pagos/libelula/callback/?transaction_id=<uuid>

    El microle de Libelula reenvía aquí la notificación de pago exitoso.
    El query param `transaction_id` corresponde al `identificador` (UUID)
    que enviamos al registrar la deuda, guardado en Factura.codigo_transaccion_pasarela.

    El callback solo llega cuando el pago fue exitoso, por lo que
    no necesitamos verificar un campo `estado`.
    """
    permission_classes = [AllowAny]

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        transaction_id = request.query_params.get('transaction_id')

        logger.warning(
            "LIBELULA CALLBACK recibido. Params: %s | Headers: %s",
            dict(request.query_params),
            dict(request.headers),
        )

        if not transaction_id:
            return Response(
                {"detail": "El parámetro 'transaction_id' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            factura = (
                Factura.objects
                .select_for_update()
                .get(codigo_transaccion_pasarela=transaction_id)
            )
        except Factura.DoesNotExist:
            logger.warning("Callback Libelula: transaction_id no encontrado: %s", transaction_id)
            return Response(
                {"detail": "Transacción no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Idempotencia: ignorar si ya fue procesada
        if factura.estado_pago != 'pendiente':
            logger.info(
                "Callback Libelula: factura %s ya procesada (estado=%s). Ignorando.",
                factura.id, factura.estado_pago,
            )
            return Response({"detail": "Ya procesado."}, status=status.HTTP_200_OK)

        tickets = list(factura.tickets.select_related('asiento', 'zona').all())

        # Confirmar pago: activar tickets y ocupar asientos
        factura.estado_pago = 'pagado'
        factura.save(update_fields=['estado_pago', 'updated_at'])

        for ticket in tickets:
            ticket.estado = 'activo'
            ticket.save(update_fields=['estado', 'updated_at'])

            if ticket.asiento:
                ticket.asiento.estado = 'ocupado'
                ticket.asiento.save(update_fields=['estado', 'updated_at'])

        logger.info(
            "Callback Libelula: factura %s confirmada. %d ticket(s) activados.",
            factura.id, len(tickets),
        )
        return Response(
            {"detail": "Pago confirmado. Tickets activados."},
            status=status.HTTP_200_OK,
        )
