from django.db import models
from django.contrib.auth.models import BaseUserManager


class SoftDeleteManager(models.Manager):
    """
    Manager que filtra automáticamente los registros con soft-delete.
    Solo retorna registros donde deleted_at es NULL (no eliminados).
    """
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager):
    """
    Manager que retorna TODOS los registros, incluyendo los eliminados.
    Usar: MiModelo.all_objects.all() para ver los eliminados también.
    """
    pass


class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para el modelo Usuario.
    Se requiere email para la creación de usuarios.
    También aplica soft-delete por defecto.
    """
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        if not username:
            raise ValueError('El username es obligatorio')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)
