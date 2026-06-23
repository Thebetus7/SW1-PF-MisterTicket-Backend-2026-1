from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import LiquidacionViewSet, LibelulaCallbackView, LibelulaRetornoView

router = DefaultRouter()
router.register(r'liquidaciones', LiquidacionViewSet, basename='liquidacion')

urlpatterns = [
    # Webhook público — Libélula POST cuando el pago se confirma
    path('libelula/callback/', LibelulaCallbackView.as_view(), name='libelula-callback'),

    # Página puente — Libélula redirige aquí al terminar; esta redirige al deep-link
    path('libelula/retorno/', LibelulaRetornoView.as_view(), name='libelula-retorno'),

    path('', include(router.urls)),
]
