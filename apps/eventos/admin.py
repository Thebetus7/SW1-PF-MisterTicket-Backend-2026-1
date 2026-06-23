from django.contrib import admin
from .models import (
    Departamento, Lugar, GeneroMusical, Evento, Zona, Asiento,
    PresentacionEvento, VerificadorEvento, RegistroAcceso
)


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'is_deleted')
    search_fields = ('nombre',)


@admin.register(Lugar)
class LugarAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'direccion', 'capacidad_total', 'departamento', 'is_deleted')
    search_fields = ('nombre',)
    list_filter = ('departamento',)


@admin.register(GeneroMusical)
class GeneroMusicalAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'is_deleted')
    search_fields = ('nombre',)


class ZonaInline(admin.TabularInline):
    model = Zona
    extra = 1


class PresentacionInline(admin.TabularInline):
    model = PresentacionEvento
    extra = 1


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'estado', 'lugar', 'promotor', 'created_at', 'is_deleted')
    search_fields = ('nombre',)
    list_filter = ('estado', 'deleted_at')
    inlines = [ZonaInline, PresentacionInline]


@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'precio', 'capacidad_max', 'entradas_disponibles', 'es_numerada', 'evento', 'is_deleted')
    list_filter = ('es_numerada', 'evento')


@admin.register(Asiento)
class AsientoAdmin(admin.ModelAdmin):
    list_display = ('id', 'fila', 'columna', 'estado', 'zona', 'is_deleted')
    list_filter = ('estado', 'zona')


@admin.register(PresentacionEvento)
class PresentacionEventoAdmin(admin.ModelAdmin):
    list_display = ('id', 'artista', 'evento', 'orden_aparicion', 'tiempo_inicio', 'is_deleted')
    list_filter = ('evento',)


@admin.register(VerificadorEvento)
class VerificadorEventoAdmin(admin.ModelAdmin):
    list_display = ('id', 'verificador', 'evento', 'is_deleted')
    list_filter = ('evento',)


@admin.register(RegistroAcceso)
class RegistroAccesoAdmin(admin.ModelAdmin):
    list_display = ('id', 'resultado', 'verificador_evento', 'ticket', 'created_at', 'is_deleted')
    list_filter = ('resultado',)
