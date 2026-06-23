from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CancionViewSet

router = DefaultRouter()
router.register('canciones', CancionViewSet, basename='cancion')

urlpatterns = [
    path('', include(router.urls)),
]
