from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static


def home(request):
    return JsonResponse({
        "message": "Bienvenido a la API de MisterTicket",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/usuarios/login/",
            "registro": "/api/usuarios/registro/",
            "usuarios": "/api/usuarios/",
            "eventos": "/api/eventos/",
            "tickets": "/api/tickets/",
            "pagos": "/api/pagos/",
        }
    })


urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),

    # Apps
    path('api/usuarios/', include('usuarios.urls')),
    path('api/eventos/', include('eventos.urls')),
    path('api/tickets/', include('tickets.urls')),
    path('api/pagos/', include('pagos.urls')),
    path('api/musica/', include('musica.urls')),
]

# Servir archivos media en desarrollo (fotos de artistas, etc.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
