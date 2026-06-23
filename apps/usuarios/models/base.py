from django.db import models
from django.utils import timezone
from usuarios.managers import SoftDeleteManager, AllObjectsManager


class SoftDeleteModel(models.Model):
    """
    Modelo abstracto que implementa soft-delete.
    En vez de borrar registros de la BD, se marca el campo 'deleted_at'.
    """
    deleted_at = models.DateTimeField(
        null=True, blank=True, default=None,
        verbose_name='Fecha de eliminación',
        help_text='Si tiene valor, el registro está soft-deleted'
    )

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft delete: marca el campo deleted_at en lugar de eliminar"""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self, using=None, keep_parents=False):
        """Elimina permanentemente el registro de la base de datos"""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Restaura un registro soft-deleted"""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self):
        return self.deleted_at is not None
