"""
Management command: limpiar_reservas
=====================================
Expira facturas en estado 'pendiente' con más de EXPIRACION_MINUTOS minutos
de antigüedad y libera los asientos y cupos que habían sido reservados.

Uso:
    python manage.py limpiar_reservas
    python manage.py limpiar_reservas --minutos 30   # umbral personalizado

Ejecución recomendada (cron cada 5 minutos):
    */5 * * * * /ruta/al/venv/bin/python /ruta/al/proyecto/manage.py limpiar_reservas
"""

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from tickets.models import Factura

logger = logging.getLogger(__name__)

EXPIRACION_MINUTOS_DEFAULT = 15


class Command(BaseCommand):
    help = 'Cancela reservas (facturas pendientes) que superaron el tiempo de expiración.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutos',
            type=int,
            default=EXPIRACION_MINUTOS_DEFAULT,
            help=f'Minutos de gracia antes de expirar una reserva (default: {EXPIRACION_MINUTOS_DEFAULT})',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se cancela sin hacer cambios reales en la BD.',
        )

    def handle(self, *args, **options):
        minutos = options['minutos']
        dry_run = options['dry_run']
        umbral = timezone.now() - timedelta(minutes=minutos)

        facturas_expiradas = Factura.objects.filter(
            estado_pago='pendiente',
            created_at__lt=umbral,
        ).prefetch_related('tickets__asiento', 'tickets__zona')

        total = facturas_expiradas.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('No hay reservas expiradas.'))
            return

        self.stdout.write(
            f'Encontradas {total} factura(s) pendientes con más de {minutos} min. '
            f'{"[DRY-RUN]" if dry_run else "Procesando..."}'
        )

        canceladas = 0
        tickets_liberados = 0

        for factura in facturas_expiradas:
            if dry_run:
                self.stdout.write(
                    f'  [DRY-RUN] Factura #{factura.id} — {factura.tickets.count()} ticket(s)'
                )
                continue

            try:
                self._cancelar_factura(factura)
                canceladas += 1
                tickets_liberados += factura.tickets.count()
                self.stdout.write(f'  ✓ Factura #{factura.id} cancelada.')
            except Exception as exc:
                logger.error('Error cancelando factura #%s: %s', factura.id, exc)
                self.stderr.write(f'  ✗ Error en factura #{factura.id}: {exc}')

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Listo. {canceladas}/{total} factura(s) canceladas, '
                    f'{tickets_liberados} ticket(s) liberados.'
                )
            )

    @transaction.atomic
    def _cancelar_factura(self, factura: Factura) -> None:
        """
        Cancela una factura expirada de forma atómica:
          1. Marca la factura como 'cancelada'.
          2. Marca los tickets como 'cancelado'.
          3. Devuelve los asientos numerados a 'disponible'.
          4. Restaura el cupo (entradas_disponibles) en cada Zona afectada.
        """
        from eventos.models import Zona  # import local para evitar circular

        # Recargar con lock para evitar race conditions con el webhook
        factura = Factura.objects.select_for_update().get(pk=factura.pk)

        # Si entre la consulta inicial y el lock otro proceso la procesó, saltar
        if factura.estado_pago != 'pendiente':
            return

        factura.estado_pago = 'cancelada'
        factura.save(update_fields=['estado_pago', 'updated_at'])

        zona_conteo: dict[int, int] = {}

        for ticket in factura.tickets.select_related('asiento', 'zona').all():
            ticket.estado = 'cancelado'
            ticket.save(update_fields=['estado', 'updated_at'])

            if ticket.asiento:
                ticket.asiento.estado = 'disponible'
                ticket.asiento.save(update_fields=['estado', 'updated_at'])

            zona_conteo[ticket.zona_id] = zona_conteo.get(ticket.zona_id, 0) + 1

        # Restaurar cupos por zona en una sola query por zona
        for zona_id, cupos in zona_conteo.items():
            Zona.objects.filter(pk=zona_id).update(
                entradas_disponibles=F('entradas_disponibles') + cupos
            )
