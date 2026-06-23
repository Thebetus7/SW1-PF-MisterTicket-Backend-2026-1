import math
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from eventos.models import Departamento, Lugar, Evento, Zona, Asiento
from usuarios.models import Promotor


class Command(BaseCommand):
    help = 'Crea departamentos, lugares, y 2 eventos de ejemplo publicados con sus zonas y asientos.'

    def handle(self, *args, **kwargs):
        # 1. Crear Departamentos de Bolivia
        departamentos_data = [
            'La Paz', 'Santa Cruz', 'Cochabamba', 
            'Oruro', 'Potosí', 'Tarija', 
            'Chuquisaca', 'Beni', 'Pando'
        ]
        
        deptos_creados = {}
        for nombre in departamentos_data:
            depto, created = Departamento.objects.get_or_create(nombre=nombre)
            deptos_creados[nombre] = depto
            if created:
                self.stdout.write(self.style.SUCCESS(f'Departamento creado: {nombre}'))

        # 2. Crear Lugares de Eventos
        lugares_data = [
            {
                'nombre': 'Estadio Hernando Siles',
                'direccion': 'Calle Claudio Sanjinés, Miraflores',
                'capacidad_total': 300,
                'departamento': deptos_creados['La Paz']
            },
            {
                'nombre': 'Coliseo Bicentenario',
                'direccion': 'Av. Monseñor Rivero, 3er anillo',
                'capacidad_total': 250,
                'departamento': deptos_creados['Santa Cruz']
            },
            {
                'nombre': 'Feria Internacional de Cochabamba',
                'direccion': 'Av. Beijing, Zona Temporal',
                'capacidad_total': 200,
                'departamento': deptos_creados['Cochabamba']
            },
            {
                'nombre': 'Centro de Convenciones Tarija',
                'direccion': 'Av. La Paz esq. Calle Sucre',
                'capacidad_total': 150,
                'departamento': deptos_creados['Tarija']
            },
            {
                'nombre': 'Teatro Gran Mariscal',
                'direccion': 'Plaza 25 de Mayo, Sucre',
                'capacidad_total': 120,
                'departamento': deptos_creados['Chuquisaca']
            }
        ]

        lugares_creados = {}
        for data in lugares_data:
            lugar, created = Lugar.objects.get_or_create(
                nombre=data['nombre'],
                defaults={
                    'direccion': data['direccion'],
                    'capacidad_total': data['capacidad_total'],
                    'departamento': data['departamento']
                }
            )
            lugares_creados[data['nombre']] = lugar
            if created:
                self.stdout.write(self.style.SUCCESS(f"Lugar creado: {data['nombre']} (Capacidad: {data['capacidad_total']})"))

        # 3. Obtener Promotores para asignar los eventos
        promotores = list(Promotor.objects.all())
        if not promotores:
            self.stdout.write(self.style.ERROR(
                "Error: No existen promotores creados en la base de datos. Ejecuta 'python manage.py seed_admin' primero."
            ))
            return

        promotor_1 = promotores[0]
        promotor_2 = promotores[1] if len(promotores) > 1 else promotor_1

        # 4. Crear Eventos de Ejemplo
        ahora = timezone.now()
        eventos_data = [
            {
                'nombre': 'Rock Fest Bolivia 2026',
                'estado': 'publicado',
                'lugar': lugares_creados['Estadio Hernando Siles'],
                'promotor': promotor_1,
                'fecha_inicio': ahora + timedelta(days=15, hours=20),
                'fecha_fin': ahora + timedelta(days=15, hours=24),
                'zonas': [
                    {'nombre': 'VIP', 'precio': 300.00, 'cantidad': 50},
                    {'nombre': 'General', 'precio': 120.00, 'cantidad': 150}
                ]
            },
            {
                'nombre': 'Festival Folclórico Nacional',
                'estado': 'publicado',
                'lugar': lugares_creados['Teatro Gran Mariscal'],
                'promotor': promotor_2,
                'fecha_inicio': ahora + timedelta(days=30, hours=19),
                'fecha_fin': ahora + timedelta(days=30, hours=23),
                'zonas': [
                    {'nombre': 'Platea', 'precio': 200.00, 'cantidad': 40},
                    {'nombre': 'Mezzanine', 'precio': 100.00, 'cantidad': 60}
                ]
            }
        ]

        for ev_data in eventos_data:
            evento, ev_created = Evento.objects.get_or_create(
                nombre=ev_data['nombre'],
                defaults={
                    'estado': ev_data['estado'],
                    'lugar': ev_data['lugar'],
                    'promotor': ev_data['promotor'],
                    'fecha_inicio': ev_data['fecha_inicio'],
                    'fecha_fin': ev_data['fecha_fin']
                }
            )

            if ev_created:
                self.stdout.write(self.style.SUCCESS(f"Evento creado: '{evento.nombre}'"))
                # Crear Zonas y Asientos
                self._crear_zonas_y_asientos(evento, ev_data['zonas'])
            else:
                self.stdout.write(self.style.WARNING(f"El evento '{evento.nombre}' ya existe."))

        self.stdout.write(self.style.SUCCESS('====== SEED DE EVENTOS COMPLETADO ======'))

    def _crear_zonas_y_asientos(self, evento, zonas_data):
        for zona_data in zonas_data:
            cantidad_asientos = zona_data['cantidad']
            zona = Zona.objects.create(
                evento=evento,
                nombre=zona_data['nombre'],
                precio=zona_data['precio'],
                capacidad_max=cantidad_asientos,
                entradas_disponibles=cantidad_asientos,
                es_numerada=True
            )
            self.stdout.write(self.style.SUCCESS(f"  -> Zona creada: {zona.nombre} ({cantidad_asientos} asientos)"))

            # Generar asientos físicos en BD
            cols = math.ceil(math.sqrt(cantidad_asientos))
            asientos_a_crear = []
            asientos_creados = 0
            fila = 1
            
            while asientos_creados < cantidad_asientos:
                for col in range(1, cols + 1):
                    if asientos_creados >= cantidad_asientos:
                        break
                    asientos_a_crear.append(Asiento(
                        zona=zona,
                        fila=str(fila),
                        columna=str(col),
                        estado='desocupado'
                    ))
                    asientos_creados += 1
                fila += 1
                
            Asiento.objects.bulk_create(asientos_a_crear)
            self.stdout.write(self.style.SUCCESS(f"     -> {asientos_creados} asientos desocupados generados."))
