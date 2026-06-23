import os
from django.db import models
from usuarios.models import Artista, SoftDeleteModel
from mutagen import File as MutagenFile

def cancion_archivo_upload_path(instance, filename):
    # Obtener extensión
    ext = filename.split('.')[-1]
    # Nombre del archivo único
    new_filename = f"cancion_{instance.pk or 'temp'}.{ext}"
    # Guardar bajo artistas/{artista_id}/musica/
    return os.path.join('artistas', str(instance.artista.pk), 'musica', new_filename)

class Cancion(SoftDeleteModel):
    nombre = models.CharField(max_length=255, verbose_name='Nombre de la canción')
    detalle = models.TextField(blank=True, null=True, verbose_name='Detalle o descripción')
    archivo = models.FileField(
        upload_to=cancion_archivo_upload_path,
        verbose_name='Archivo de audio',
        help_text='Sube el archivo de música (.mp3, .wav, .m4a)'
    )
    artista = models.ForeignKey(
        Artista,
        on_delete=models.CASCADE,
        related_name='canciones',
        verbose_name='Artista'
    )
    publicado = models.BooleanField(
        default=False,
        verbose_name='Publicado',
        help_text='Indica si la canción es pública para los fans'
    )
    
    # Atributos de audio extraídos automáticamente
    duracion = models.FloatField(null=True, blank=True, verbose_name='Duración (segundos)')
    tamano = models.IntegerField(null=True, blank=True, verbose_name='Tamaño (bytes)')
    formato = models.CharField(max_length=50, null=True, blank=True, verbose_name='Formato')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'canciones'
        verbose_name = 'Canción'
        verbose_name_plural = 'Canciones'
        ordering = ['-created_at']

    @property
    def archivo_url(self):
        if self.archivo and hasattr(self.archivo, 'url'):
            return self.archivo.url
        return None

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        # Primero guardamos el modelo normalmente para que se almacene el archivo y se genere el path/url
        super().save(*args, **kwargs)
        
        # Si es un registro nuevo y tiene archivo, extraemos los metadatos
        if is_new and self.archivo:
            try:
                # 1. Tamaño en bytes
                self.tamano = self.archivo.size
                
                # 2. Formato (extensión de archivo)
                ext = self.archivo.name.split('.')[-1].lower()
                self.formato = ext
                
                # 3. Duración (en segundos)
                duracion_segundos = 0.0
                
                # Intentar abrir el archivo de forma que mutagen lo lea correctamente
                try:
                    # En local con almacenamiento en disco, intentamos usar self.archivo.path
                    path_exists = False
                    try:
                        if hasattr(self.archivo, 'path') and self.archivo.path:
                            path_exists = os.path.exists(self.archivo.path)
                    except (NotImplementedError, AttributeError):
                        path_exists = False

                    if path_exists:
                        audio = MutagenFile(self.archivo.path)
                        if audio is not None and audio.info is not None:
                            duracion_segundos = audio.info.length
                    else:
                        # Si está en MinIO/S3, leemos el archivo en memoria usando self.archivo.open()
                        self.archivo.open()
                        audio = MutagenFile(self.archivo)
                        if audio is not None and audio.info is not None:
                            duracion_segundos = audio.info.length
                except Exception as ex:
                    print(f"[MUTAGEN] >> Error al analizar el archivo de audio con mutagen: {ex}")
                
                self.duracion = duracion_segundos
                
                # Guardar únicamente los campos de metadatos para evitar bucle de save()
                super().save(update_fields=['duracion', 'tamano', 'formato'])
            except Exception as e:
                print(f"[ERROR METADATOS AUDIO] >> No se pudieron extraer metadatos generales: {e}")

    def __str__(self):
        return f"{self.nombre} - {self.artista.nombre_artistico}"
