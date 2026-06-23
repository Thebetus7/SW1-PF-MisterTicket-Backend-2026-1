import math
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction

from ..models import Evento, Zona, Asiento
from ..serializers import EventoSerializer, EventoCrearSerializer, ZonaCrearSerializer
from .mixins import SoftDeleteMixin


class EventoViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    """
    GET    /api/eventos/eventos/         → Listar
    POST   /api/eventos/eventos/         → Crear
    GET    /api/eventos/eventos/{id}/    → Detalle (incluye zonas anidadas)
    PUT    /api/eventos/eventos/{id}/    → Actualizar
    PATCH  /api/eventos/eventos/{id}/    → Actualizar parcial
    DELETE /api/eventos/eventos/{id}/    → Soft delete
    """
    queryset = Evento.objects.select_related('lugar', 'promotor').prefetch_related('zonas')
    serializer_class = EventoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Filtro por promotor logueado
        if hasattr(user, 'perfil_promotor'):
            qs = qs.filter(promotor=user.perfil_promotor)
            
        # Filtros por fecha
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_desde:
            qs = qs.filter(fecha_inicio__date__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha_inicio__date__lte=fecha_hasta)
            
        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return EventoCrearSerializer
        return EventoSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = self.request.user
        promotor = getattr(user, 'perfil_promotor', None)

        if not promotor:
            return Response(
                {"detail": "El usuario autenticado no cuenta con un perfil de promotor y no puede crear eventos. Por favor, inicie sesión como promotor (ej. promotor1)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        evento = Evento.objects.create(
            nombre=serializer.validated_data['nombre'],
            estado=serializer.validated_data['estado'],
            lugar=serializer.validated_data['lugar'],
            fecha_inicio=serializer.validated_data['fecha_inicio'],
            fecha_fin=serializer.validated_data['fecha_fin'],
            promotor=promotor
        )

        zonas_data = serializer.validated_data['zonas']
        self._crear_zonas_y_asientos(evento, zonas_data)

        headers = self.get_success_headers(serializer.data)
        return Response(EventoSerializer(evento).data, status=status.HTTP_201_CREATED, headers=headers)

    def _crear_zonas_y_asientos(self, evento, zonas_data):
        for zona_data in zonas_data:
            cantidad_asientos = zona_data['cantidad_asientos']
            zona = Zona.objects.create(
                evento=evento,
                nombre=zona_data['nombre'],
                precio=zona_data['precio'],
                capacidad_max=cantidad_asientos,
                entradas_disponibles=cantidad_asientos,
                es_numerada=True # En este proyecto universitario forzamos a true para crear los asientos fisicos en bd
            )

            # Generar asientos
            # Calculamos columnas para layout cuadrado aproximado
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

    @action(detail=True, methods=['delete'], url_path='eliminar_zona/(?P<zona_id>[^/.]+)')
    def eliminar_zona(self, request, pk=None, zona_id=None):
        evento = self.get_object()
        try:
            zona = Zona.objects.get(id=zona_id, evento=evento)
            # Esto hará un soft delete si Zona tiene soft delete, 
            # de lo contrario hard delete. En Django cascade actua igual.
            zona.delete() 
            return Response({'detail': 'Zona y sus asientos eliminados correctamente.'}, status=status.HTTP_200_OK)
        except Zona.DoesNotExist:
            return Response({'detail': 'La zona no existe en este evento.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='agregar_zona')
    @transaction.atomic
    def agregar_zona(self, request, pk=None):
        evento = self.get_object()
        serializer = ZonaCrearSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        lugar_capacidad = evento.lugar.capacidad_total
        # Calcular asientos actuales (solo zonas activas)
        asientos_actuales = sum(z.capacidad_max for z in evento.zonas.all())
        cantidad_nueva = serializer.validated_data['cantidad_asientos']
        
        if asientos_actuales + cantidad_nueva > lugar_capacidad:
            return Response(
                {"detail": f"Capacidad excedida. Quedan {lugar_capacidad - asientos_actuales} asientos disponibles."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        self._crear_zonas_y_asientos(evento, [serializer.validated_data])
        
        return Response({'detail': 'Zona y asientos agregados correctamente.'}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='feed', permission_classes=[permissions.AllowAny])
    def feed(self, request):
        from ..serializers.evento import EventoFeedSerializer
        
        # Prefetch presentaciones y artistas para optimizar queries
        queryset = Evento.objects.filter(estado='publicado').select_related(
            'lugar', 'promotor'
        ).prefetch_related(
            'presentaciones__artista__generos_musicales',
            'presentaciones__artista__departamento_origen'
        ).order_by('-updated_at')
        
        serializer = EventoFeedSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='zonas-disponibles', permission_classes=[permissions.AllowAny])
    def zonas_disponibles(self, request, pk=None):
        from ..serializers.zona_asiento import ZonaSerializer
        evento = self.get_object()
        zonas = Zona.objects.filter(evento=evento)
        serializer = ZonaSerializer(zonas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

