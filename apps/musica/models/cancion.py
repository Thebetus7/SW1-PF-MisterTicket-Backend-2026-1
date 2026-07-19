import os
from django.db import models
from usuarios.models import Artista, SoftDeleteModel
from mutagen import File as MutagenFile
from musica.utils.analyzer import analizar_audio, calcular_similitud_coseno

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
    
    # Nuevos atributos calculados por IA Local
    bpm = models.FloatField(null=True, blank=True, verbose_name='Tempo (BPM)')
    genero_ia = models.CharField(max_length=100, null=True, blank=True, verbose_name='Género IA')
    energia_ia = models.FloatField(null=True, blank=True, verbose_name='Energía IA')
    brillo_ia = models.FloatField(null=True, blank=True, verbose_name='Brillo IA (Hz)')
    
    # Detección de Plagio e Infracciones
    vector_timbre = models.JSONField(null=True, blank=True, verbose_name='Vector de Timbre (MFCC)')
    es_plagio = models.BooleanField(default=False, verbose_name='Sospecha de Plagio')
    similitud_plagio = models.FloatField(null=True, blank=True, verbose_name='Similitud de Plagio (%)')
    plagio_de = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sospechas_plagio', verbose_name='Plagio de')
    
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
                
                # 4. Extraer métricas de IA local
                try:
                    path_para_analizar = None
                    if hasattr(self.archivo, 'path') and self.archivo.path and os.path.exists(self.archivo.path):
                        path_para_analizar = self.archivo.path
                    else:
                        # Fallback temporal si está almacenado en la nube (S3/Minio)
                        import tempfile
                        self.archivo.open()
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}') as temp_file:
                            temp_file.write(self.archivo.read())
                            path_para_analizar = temp_file.name
                    
                    if path_para_analizar:
                        resultados_ia = analizar_audio(path_para_analizar)
                        self.bpm = resultados_ia['bpm']
                        self.genero_ia = resultados_ia['genero']
                        self.energia_ia = resultados_ia['energia']
                        self.brillo_ia = resultados_ia['brillo']
                        self.vector_timbre = resultados_ia['vector_timbre']
                        
                        # --- ALGORITMO DE DETECCION DE PLAGIO ---
                        max_similitud = 0.0
                        cancion_candidata = None
                        
                        # Obtener todas las canciones activas ordenadas por creación (primera importada primero)
                        canciones_existentes = Cancion.objects.filter(
                            deleted_at__isnull=True,
                            vector_timbre__isnull=False
                        ).order_by('created_at')
                        
                        if self.pk:
                            canciones_existentes = canciones_existentes.exclude(pk=self.pk)
                            
                        for c in canciones_existentes:
                            if c.vector_timbre and len(c.vector_timbre) > 0:
                                sim = calcular_similitud_coseno(
                                    self.vector_timbre, c.vector_timbre,
                                    bpm1=self.bpm, bpm2=c.bpm,
                                    energia1=self.energia_ia, energia2=c.energia_ia,
                                    brillo1=self.brillo_ia, brillo2=c.brillo_ia
                                )
                                if sim > max_similitud:
                                    max_similitud = sim
                                    cancion_candidata = c
                                    
                        # Si la similitud tímbrica pura (sin volumen) supera el 95%
                        if max_similitud >= 95.0:
                            self.es_plagio = True
                            self.similitud_plagio = max_similitud
                            self.plagio_de = cancion_candidata
                        else:
                            self.es_plagio = False
                            self.similitud_plagio = None
                            self.plagio_de = None
                        
                        # Limpiar temporal si se generó uno
                        if not hasattr(self.archivo, 'path') or not self.archivo.path:
                            try:
                                os.unlink(path_para_analizar)
                            except Exception:
                                pass
                except Exception as ia_e:
                    print(f"[ERROR IA ANALYZER] >> Error al correr análisis de IA local: {ia_e}")
                
                # Guardar únicamente los campos de metadatos para evitar bucle de save()
                super().save(update_fields=[
                    'duracion', 'tamano', 'formato', 'bpm', 'genero_ia', 'energia_ia', 'brillo_ia',
                    'vector_timbre', 'es_plagio', 'similitud_plagio', 'plagio_de'
                ])
            except Exception as e:
                print(f"[ERROR METADATOS AUDIO] >> No se pudieron extraer metadatos generales: {e}")

    def __str__(self):
        return f"{self.nombre} - {self.artista.nombre_artistico}"
