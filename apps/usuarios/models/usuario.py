import os
from django.contrib.auth.models import AbstractUser
from django.db import models
from usuarios.managers import AllObjectsManager, UsuarioManager
from .base import SoftDeleteModel
from .persona import Persona


def usuario_foto_upload_path(instance, filename):
    """Genera una ruta única para la foto de perfil del usuario."""
    ext = filename.split('.')[-1]
    new_filename = f"foto_usuario_{instance.pk or 'temp'}.{ext}"
    return os.path.join('usuarios', 'fotos', str(instance.pk or 'temp'), new_filename)


class Usuario(AbstractUser, SoftDeleteModel):
    """
    Modelo de usuario personalizado que extiende AbstractUser.
    """
    email = models.EmailField(unique=True, verbose_name='Correo electrónico')
    persona = models.OneToOneField(
        Persona,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='usuario',
        verbose_name='Persona'
    )
    foto = models.ImageField(
        upload_to=usuario_foto_upload_path,
        blank=True, null=True,
        verbose_name='Foto de perfil',
        help_text='Avatar del usuario. Se guarda en media/usuarios/fotos/ o en MinIO/S3.'
    )

    recibir_notificaciones = models.BooleanField(
        default=True,
        verbose_name='Recibir notificaciones',
        help_text='Permite habilitar o deshabilitar la recepción de notificaciones en el sistema.'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UsuarioManager()
    all_objects = AllObjectsManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        permissions = [
            ('gestionar_eventos', 'Puede crear, editar y eliminar eventos'),
            ('verificar_tickets', 'Puede escanear y verificar tickets en el acceso'),
            ('gestionar_artistas', 'Puede administrar perfiles de artistas'),
            ('ver_reportes', 'Puede ver reportes financieros y de ventas'),
        ]

    def get_roles(self):
        """Retorna lista de nombres de los grupos/roles del usuario"""
        return list(self.groups.values_list('name', flat=True))

    def has_role(self, role_name):
        """Verifica si el usuario tiene un rol específico"""
        return self.groups.filter(name=role_name).exists()

    def assign_role(self, group):
        """Asigna un rol (Group) al usuario"""
        self.groups.add(group)

    def remove_role(self, group):
        """Remueve un rol (Group) del usuario"""
        self.groups.remove(group)

    def __str__(self):
        return self.username
