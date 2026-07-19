import os
from django.core.management.base import BaseCommand
from musica.models import Cancion
from musica.utils.analyzer import analizar_audio, calcular_similitud_coseno

class Command(BaseCommand):
    help = 'Analiza con la IA local todas las canciones existentes en la base de datos que tienen valores por defecto o vacíos'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Buscando canciones para analizar con la IA local..."))
        
        # Limpiar vectores anteriores y estados de plagio en la base de datos antes de recalcular
        self.stdout.write(self.style.NOTICE("Limpiando firmas acústicas anteriores en la base de datos para recalcular desde cero..."))
        Cancion.objects.all().update(
            vector_timbre=None, 
            es_plagio=False, 
            similitud_plagio=None, 
            plagio_de=None
        )
        
        # Obtener todas las canciones activas ordenadas por creación (primera importada primero)
        canciones = Cancion.objects.filter(deleted_at__isnull=True).order_by('created_at')
        
        if not canciones.exists():
            self.stdout.write(self.style.WARNING("No se encontraron canciones registradas en el sistema."))
            return
            
        self.stdout.write(self.style.NOTICE(f"Se encontraron {len(canciones)} canciones registradas. Procesando..."))
        
        exitos = 0
        fallas = 0
        
        for cancion in canciones:
            self.stdout.write(f"\nProcesando canción ID {cancion.id}: '{cancion.nombre}'")
            
            if not cancion.archivo:
                self.stdout.write(self.style.WARNING(f"  [OMITIDA] La canción no tiene un archivo de audio asociado."))
                continue
                
            # Determinar la ruta del archivo
            ext = cancion.archivo.name.split('.')[-1].lower()
            path_para_analizar = None
            temp_creado = False
            
            try:
                if hasattr(cancion.archivo, 'path') and cancion.archivo.path and os.path.exists(cancion.archivo.path):
                    path_para_analizar = cancion.archivo.path
                else:
                    # Fallback si está en MinIO/S3
                    import tempfile
                    self.stdout.write("  [INFO] Descargando archivo temporal de la nube...")
                    cancion.archivo.open()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}') as temp_file:
                        temp_file.write(cancion.archivo.read())
                        path_para_analizar = temp_file.name
                        temp_creado = True
                
                if path_para_analizar and os.path.exists(path_para_analizar):
                    self.stdout.write("  [PROCESANDO] Corriendo análisis acústico con Librosa...")
                    resultados = analizar_audio(path_para_analizar)
                    
                    # Asignar resultados
                    cancion.bpm = resultados['bpm']
                    cancion.genero_ia = resultados['genero']
                    cancion.energia_ia = resultados['energia']
                    cancion.brillo_ia = resultados['brillo']
                    cancion.vector_timbre = resultados['vector_timbre']
                    
                    # --- ALGORITMO DE DETECCION DE PLAGIO ---
                    max_similitud = 0.0
                    cancion_candidata = None
                    
                    # Comparar contra canciones que YA tienen vector y que no son el registro actual, ordenadas cronológicamente
                    canciones_para_comparar = Cancion.objects.filter(
                        deleted_at__isnull=True,
                        vector_timbre__isnull=False
                    ).exclude(pk=cancion.pk).order_by('created_at')
                    
                    for c in canciones_para_comparar:
                        if c.vector_timbre and len(c.vector_timbre) > 0:
                            sim = calcular_similitud_coseno(
                                cancion.vector_timbre, c.vector_timbre,
                                bpm1=cancion.bpm, bpm2=c.bpm,
                                energia1=cancion.energia_ia, energia2=c.energia_ia,
                                brillo1=cancion.brillo_ia, brillo2=c.brillo_ia
                            )
                            if sim > max_similitud:
                                max_similitud = sim
                                cancion_candidata = c
                                
                    if max_similitud >= 95.0:
                        cancion.es_plagio = True
                        cancion.similitud_plagio = max_similitud
                        cancion.plagio_de = cancion_candidata
                        self.stdout.write(self.style.WARNING(
                            f"  [ALERTA PLAGIO] Coincidencia detectada con '{cancion_candidata.nombre}' al {max_similitud}%"
                        ))
                    else:
                        cancion.es_plagio = False
                        cancion.similitud_plagio = None
                        cancion.plagio_de = None
                    
                    # Guardar en base de datos todos los campos calculados por la IA
                    cancion.save(update_fields=[
                        'bpm', 'genero_ia', 'energia_ia', 'brillo_ia', 
                        'vector_timbre', 'es_plagio', 'similitud_plagio', 'plagio_de'
                    ])
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"  [EXITO] IA actualizo: {cancion.genero_ia} | {cancion.bpm} BPM | {cancion.energia_ia * 100:.0f}% energia | {cancion.brillo_ia:.0f} Hz brillo"
                    ))
                    exitos += 1
                else:
                    self.stdout.write(self.style.ERROR(f"  [ERROR] No se pudo acceder al archivo físico de audio."))
                    fallas += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  [FALLO] Error al procesar la canción: {e}"))
                fallas += 1
            finally:
                # Limpiar archivo temporal si se creó uno
                if temp_creado and path_para_analizar and os.path.exists(path_para_analizar):
                    try:
                        os.unlink(path_para_analizar)
                    except Exception:
                        pass
                        
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"Proceso finalizado. Canciones actualizadas con IA: {exitos} | Errores: {fallas}"))
        self.stdout.write("="*50)
