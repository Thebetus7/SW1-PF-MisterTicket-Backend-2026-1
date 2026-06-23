import uuid
import logging

import stripe
import requests
from django.conf import settings
from django.db import transaction
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from ..models import Ticket, Factura
from ..serializers.compra import (
    CompraRequestSerializer,
    CompraResponseSerializer,
    ReservaResponseSerializer,
)
from eventos.models import Asiento

logger = logging.getLogger(__name__)

LIBELULA_REGISTRAR_URL = (
    "https://ycv134zb2c.execute-api.us-east-1.amazonaws.com"
    "/dev/api/libelula/deuda/registrar"
)


class CompraView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = CompraRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        metodo_pago = serializer.validated_data['metodo_pago']
        if metodo_pago == 'stripe':
            return self._pagar_con_stripe(request, serializer.validated_data)
        return self._pagar_con_libelula(request, serializer.validated_data)

    # ------------------------------------------------------------------
    # Flujo Stripe
    # ------------------------------------------------------------------
    def _pagar_con_stripe(self, request, data):
        zona = data['zona']
        cantidad = data['cantidad']
        payment_method_id = data['payment_method_id']
        monto_total = zona.precio * cantidad

        if payment_method_id == "pm_desarrollo_directo":
            intent_id = "pi_dev_" + uuid.uuid4().hex[:12].upper()
        else:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            if not stripe.api_key:
                return Response(
                    {"detail": "STRIPE_SECRET_KEY no configurado."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            try:
                intent = stripe.PaymentIntent.create(
                    amount=int(monto_total * 100),
                    currency='bob',
                    payment_method=payment_method_id,
                    confirm=True,
                    automatic_payment_methods={'enabled': True, 'allow_redirects': 'never'},
                )
            except stripe.error.CardError as e:
                return Response(
                    {"detail": "Error de tarjeta: " + str(e.user_message or e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except stripe.error.StripeError as e:
                return Response(
                    {"detail": "Error Stripe: " + str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if intent.status != 'succeeded':
                return Response(
                    {"detail": "Pago no completado. Estado: " + intent.status},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            intent_id = intent.id

        factura = Factura.objects.create(
            precio=monto_total,
            estado_pago='pagado',
            cliente=request.user,
            stripe_payment_intent_id=intent_id,
        )
        self._crear_tickets(zona, cantidad, factura, request.user, 'activo', 'ocupado')
        zona.entradas_disponibles -= cantidad
        zona.save(update_fields=['entradas_disponibles', 'updated_at'])
        return Response(CompraResponseSerializer(factura).data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # Flujo Libelula
    # ------------------------------------------------------------------
    def _pagar_con_libelula(self, request, data):
        zona = data['zona']
        cantidad = data['cantidad']
        monto_total = zona.precio * cantidad
        codigo_transaccion = uuid.uuid4()

        factura = Factura.objects.create(
            precio=monto_total,
            estado_pago='pendiente',
            cliente=request.user,
            codigo_transaccion_pasarela=codigo_transaccion,
        )
        self._crear_tickets(zona, cantidad, factura, request.user, 'reservado', 'reservado')
        zona.entradas_disponibles -= cantidad
        zona.save(update_fields=['entradas_disponibles', 'updated_at'])

        usuario = request.user
        nombre_cliente = usuario.first_name or ''
        apellido_cliente = usuario.last_name or ''
        if not nombre_cliente and hasattr(usuario, 'persona') and usuario.persona:
            partes = usuario.persona.nombre.split(' ', 1)
            nombre_cliente = partes[0]
            apellido_cliente = partes[1] if len(partes) > 1 else ''
        if not nombre_cliente:
            nombre_cliente = usuario.username

        payload = {
            "identificador": str(codigo_transaccion),
            "email_cliente": usuario.email,
            "nombre_cliente": nombre_cliente,
            "apellido_cliente": apellido_cliente,
            "descripcion": "Compra {} ticket(s) - {} - Factura #{}".format(
                cantidad, zona.nombre, factura.id),
            "lineas_detalle_deuda": [
                {
                    "concepto": "Ticket - {} - {}".format(zona.nombre, zona.evento.nombre),
                    "cantidad": cantidad,
                    "costo_unitario": 0.10,
                    "descuento_unitario": 0,
                    "codigo_producto": "ZONA-{}".format(zona.id),
                }
            ],
            "api_key": getattr(settings, 'LIBELULA_API_KEY', ''),
        }

        try:
            resp = requests.post(
                LIBELULA_REGISTRAR_URL,
                json=payload,
                timeout=15,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            libelula_data = resp.json()
        except requests.exceptions.Timeout:
            logger.error("Timeout Libelula. Factura=%s", factura.id)
            raise Exception("La pasarela no respondio a tiempo. Intente de nuevo.")
        except requests.exceptions.RequestException as exc:
            logger.error("Error Libelula. Factura=%s. %s", factura.id, exc)
            raise Exception("Error al comunicarse con la pasarela: {}".format(exc))

        url_pasarela = libelula_data.get('url_pasarela_pagos') or libelula_data.get('url')
        if not url_pasarela:
            logger.error("Libelula sin URL. Resp: %s", libelula_data)
            raise Exception("Libelula no devolvio la URL de pago. Intente de nuevo.")

        return Response(
            ReservaResponseSerializer({
                'factura_id': factura.id,
                'codigo_transaccion_pasarela': codigo_transaccion,
                'precio_total': monto_total,
                'estado_pago': factura.estado_pago,
                'url_pasarela_pagos': url_pasarela,
            }).data,
            status=status.HTTP_201_CREATED,
        )

    # ------------------------------------------------------------------
    # Helper compartido
    # ------------------------------------------------------------------
    def _crear_tickets(self, zona, cantidad, factura, propietario, estado_ticket, estado_asiento):
        tickets = []
        if zona.es_numerada:
            asientos_libres = list(
                Asiento.objects.select_for_update()
                .filter(zona=zona, estado__in=['disponible', 'desocupado'])
                .order_by('fila', 'columna')[:cantidad]
            )
            if len(asientos_libres) < cantidad:
                raise Exception("No hay suficientes asientos. Intente de nuevo.")
            for asiento in asientos_libres:
                asiento.estado = estado_asiento
                asiento.save(update_fields=['estado', 'updated_at'])
                tickets.append(Ticket.objects.create(
                    codigo_qr="MT-" + uuid.uuid4().hex[:12].upper(),
                    estado=estado_ticket,
                    asiento=asiento,
                    zona=zona,
                    factura=factura,
                    propietario=propietario,
                ))
        else:
            for _ in range(cantidad):
                tickets.append(Ticket.objects.create(
                    codigo_qr="MT-" + uuid.uuid4().hex[:12].upper(),
                    estado=estado_ticket,
                    asiento=None,
                    zona=zona,
                    factura=factura,
                    propietario=propietario,
                ))
        return tickets

    def handle_exception(self, exc):
        if isinstance(exc, Exception) and not hasattr(exc, 'status_code'):
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return super().handle_exception(exc)
