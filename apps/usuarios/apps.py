from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'
    verbose_name = 'Gestión de Usuarios'

    def ready(self):
        """
        Se ejecuta cuando la app está lista.
        Conecta la señal post_migrate para crear roles y permisos automáticamente.
        """
        from django.db.models.signals import post_migrate
        post_migrate.connect(crear_roles_y_permisos, sender=self)


def crear_roles_y_permisos(sender, **kwargs):
    """
    ═══════════════════════════════════════════════════════════════
    CREACIÓN AUTOMÁTICA DE ROLES Y PERMISOS
    ═══════════════════════════════════════════════════════════════
    
    Esta función se ejecuta después de cada 'migrate'.
    Crea los 3 roles (Groups) y asigna los 4 permisos personalizados.
    
    EQUIVALENCIA CON LARAVEL/SPATIE:
    ─────────────────────────────────
    Laravel (Spatie):                     Django:
    ─────────────                         ───────
    Role::create(['name' => 'admin'])  → Group.objects.get_or_create(name='admin')
    Permission::create(['name' => ..]) → Permission.objects.get(codename=...)
    $role->givePermissionTo(...)        → group.permissions.add(...)
    $user->assignRole('organizador')   → user.groups.add(grupo_organizador)
    $user->hasRole('organizador')      → user.groups.filter(name='organizador').exists()
    $user->hasPermissionTo('...')      → user.has_perm('usuarios.gestionar_eventos')
    ═══════════════════════════════════════════════════════════════
    """
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    try:
        # Obtener el ContentType del modelo Usuario para buscar los permisos custom
        from usuarios.models import Usuario
        ct = ContentType.objects.get_for_model(Usuario)

        # ─── CREAR LOS 4 ROLES (Groups) ───
        rol_promotor, _ = Group.objects.get_or_create(name='promotor')
        rol_verificador, _ = Group.objects.get_or_create(name='verificador')
        rol_artista, _ = Group.objects.get_or_create(name='artista')
        rol_fan, _ = Group.objects.get_or_create(name='fan')

        # ─── OBTENER LOS 4 PERMISOS CUSTOM ───
        # Estos permisos se definen en Meta.permissions del modelo Usuario
        permisos = {}
        for codename in ['gestionar_eventos', 'verificar_tickets', 'gestionar_artistas', 'ver_reportes']:
            try:
                permisos[codename] = Permission.objects.get(
                    codename=codename,
                    content_type=ct
                )
            except Permission.DoesNotExist:
                # Los permisos aún no se han creado (primera migración)
                return

        # ─── ASIGNAR PERMISOS A CADA ROL ───
        # Promotor: puede gestionar eventos y ver reportes
        rol_promotor.permissions.set([
            permisos['gestionar_eventos'],
            permisos['ver_reportes'],
        ])

        # Verificador: puede verificar tickets
        rol_verificador.permissions.set([
            permisos['verificar_tickets'],
        ])

        # Artista: puede gestionar su perfil de artista y ver reportes
        rol_artista.permissions.set([
            permisos['gestionar_artistas'],
            permisos['ver_reportes'],
        ])

        print("[OK] Roles y permisos creados/actualizados correctamente.")

    except Exception as e:
        # En la primera migración puede que los modelos aún no existan
        print(f"[WARNING] No se pudieron crear roles/permisos (normal en primera migración): {e}")
