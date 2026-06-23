from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Persona, Artista, Promotor, Verificador


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'ci', 'created_at', 'is_deleted')
    search_fields = ('nombre', 'ci')
    list_filter = ('deleted_at',)

    def is_deleted(self, obj):
        return obj.is_deleted
    is_deleted.boolean = True
    is_deleted.short_description = 'Eliminado'


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'persona', 'get_roles_display', 'is_active', 'is_deleted')
    list_filter = ('groups', 'is_active', 'deleted_at')
    search_fields = ('username', 'email', 'persona__nombre')

    fieldsets = UserAdmin.fieldsets + (
        ('MisterTicket', {
            'fields': ('persona', 'deleted_at'),
        }),
    )

    def get_roles_display(self, obj):
        roles = obj.get_roles()
        return ', '.join(roles) if roles else 'Sin rol'
    get_roles_display.short_description = 'Roles'

    def is_deleted(self, obj):
        return obj.is_deleted
    is_deleted.boolean = True
    is_deleted.short_description = 'Eliminado'


@admin.register(Artista)
class ArtistaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_artistico', 'usuario', 'foto_url', 'is_deleted')
    search_fields = ('nombre_artistico',)
    list_filter = ('deleted_at',)
    filter_horizontal = ('generos_musicales',)


@admin.register(Promotor)
class PromotorAdmin(admin.ModelAdmin):
    list_display = ('id', 'razon_social', 'nit_rfc', 'usuario', 'is_deleted')
    search_fields = ('razon_social', 'nit_rfc')
    list_filter = ('deleted_at',)


@admin.register(Verificador)
class VerificadorAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'promotor', 'pago', 'estado', 'is_deleted')
    search_fields = ('usuario__username', 'promotor__razon_social')
    list_filter = ('estado', 'deleted_at')
