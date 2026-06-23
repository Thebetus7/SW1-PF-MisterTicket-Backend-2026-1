from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DepartamentoViewSet, LugarViewSet, GeneroMusicalViewSet,
    EventoViewSet, ZonaViewSet, AsientoViewSet,
    PresentacionEventoViewSet, VerificadorEventoViewSet, RegistroAccesoViewSet,
)

router = DefaultRouter()
router.register(r'departamentos', DepartamentoViewSet, basename='departamento')
router.register(r'lugares', LugarViewSet, basename='lugar')
router.register(r'generos', GeneroMusicalViewSet, basename='genero-musical')
router.register(r'eventos', EventoViewSet, basename='evento')
router.register(r'zonas', ZonaViewSet, basename='zona')
router.register(r'asientos', AsientoViewSet, basename='asiento')
router.register(r'presentaciones', PresentacionEventoViewSet, basename='presentacion')
router.register(r'verificadores-evento', VerificadorEventoViewSet, basename='verificador-evento')
router.register(r'registros-acceso', RegistroAccesoViewSet, basename='registro-acceso')

urlpatterns = [
    path('', include(router.urls)),
]
