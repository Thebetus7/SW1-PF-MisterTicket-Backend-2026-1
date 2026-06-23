from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import FacturaViewSet, TicketViewSet, CompraView

router = DefaultRouter()
router.register(r'facturas', FacturaViewSet, basename='factura')
router.register(r'tickets', TicketViewSet, basename='ticket')

urlpatterns = [
    path('comprar/', CompraView.as_view(), name='comprar-ticket'),
    path('', include(router.urls)),
]

