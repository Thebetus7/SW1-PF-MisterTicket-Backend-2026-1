import os
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .base import SoftDeleteModel
from .usuario import Usuario


def artista_foto_upload_path(instance, filename):
    # Obtener la extensión del archivo original
    ext = filename.split('.')[-1]
    # Generar un nombre único usando el ID del artista
    new_filename = f"foto_artista_{instance.pk or 'temp'}.{ext}"
    return os.path.join('artistas', 'fotos', str(instance.pk or 'temp'), new_filename)


class Artista(SoftDeleteModel):
    """
    Perfil de artista. Puede o no estar vinculado a un usuario del sistema.
    """
    nombre_artistico = models.CharField(max_length=255, verbose_name='Nombre artístico')
    biografia = models.TextField(blank=True, null=True, verbose_name='Biografía')
    
    foto = models.ImageField(
        upload_to=artista_foto_upload_path,
        blank=True, null=True,
        verbose_name='Foto del artista',
        help_text='Imagen de perfil del artista. Se guarda en media/artistas/fotos/'
    )

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='perfil_artista',
        verbose_name='Usuario vinculado'
    )

    # Relación muchos a muchos con GeneroMusical (tabla intermedia)
    generos_musicales = models.ManyToManyField(
        'eventos.GeneroMusical',
        blank=True,
        related_name='artistas',
        verbose_name='Géneros musicales',
        db_table='artista_genero_musical'
    )

    departamento_origen = models.ForeignKey(
        'eventos.Departamento',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='artistas_origen',
        verbose_name='Departamento de origen'
    )

    popularidad = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Popularidad',
        help_text='Popularidad del artista de 0 a 100'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'artistas'
        verbose_name = 'Artista'
        verbose_name_plural = 'Artistas'

    @property
    def foto_url(self):
        if self.foto and hasattr(self.foto, 'url'):
            return self.foto.url
        return None

    def __str__(self):
        return self.nombre_artistico
