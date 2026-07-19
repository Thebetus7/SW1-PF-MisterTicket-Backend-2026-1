import os
import sys

# Inyectar dinámicamente imageio-ffmpeg en el PATH del sistema para permitir decodificar formatos comprimidos (M4A, MP3, etc.)
try:
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(ffmpeg_exe)
    
    # Crear un alias estándar llamado ffmpeg.exe en el mismo directorio si no existe para que audioread lo encuentre
    standard_ffmpeg = os.path.join(ffmpeg_dir, "ffmpeg.exe")
    if not os.path.exists(standard_ffmpeg):
        try:
            os.link(ffmpeg_exe, standard_ffmpeg)
            print(f"[IA ANALYZER] Creado enlace físico de FFmpeg en: {standard_ffmpeg}")
        except Exception:
            try:
                import shutil
                shutil.copy(ffmpeg_exe, standard_ffmpeg)
                print(f"[IA ANALYZER] Copiado FFmpeg de fallback en: {standard_ffmpeg}")
            except Exception as e:
                print(f"[IA ANALYZER] No se pudo crear el alias ffmpeg.exe: {e}")
                
    if ffmpeg_dir not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + ffmpeg_dir
    print(f"[IA ANALYZER] Enlazado decodificador portable FFmpeg desde: {ffmpeg_dir}")
except ImportError:
    print("[IA ANALYZER] Alerta: imageio_ffmpeg no está instalado, la decodificación de formatos comprimidos puede fallar.")

import numpy as np
import librosa
import joblib
from django.conf import settings

# Ruta del modelo de IA pre-entrenado
MODEL_DIR = os.path.join(settings.BASE_DIR, 'core', 'ia_models')
MODEL_PATH = os.path.join(MODEL_DIR, 'genero_classifier.joblib')

def analizar_audio(file_path):
    """
    Analiza un archivo de audio local utilizando Librosa para extraer:
    - bpm (float): Beats Per Minute estimado.
    - energia (float): Amplitud RMS promedio (rango aproximado 0.0 a 1.0).
    - brillo (float): Centroide espectral promedio (Hz).
    - genero (str): Género predicho (Rock, Pop, Jazz, Electronic, Reggaeton, etc.).
    - vector_timbre (list): Firma espectral tímbrica promedio (13 MFCCs).
    
    Para optimizar el uso de memoria y tiempo de CPU, solo se analizan
    los primeros 30 segundos del archivo de audio.
    """
    # Resultado por defecto si hay un error crítico
    resultado = {
        'bpm': 120.0,
        'energia': 0.5,
        'brillo': 1500.0,
        'genero': 'Desconocido',
        'vector_timbre': [0.0] * 13
    }
    
    if not os.path.exists(file_path):
        print(f"[IA ANALYZER] El archivo no existe en la ruta: {file_path}")
        return resultado

    try:
        print(f"[IA ANALYZER] Iniciando análisis acústico local de: {file_path}")
        # Cargar los primeros 30 segundos del audio (para ahorrar memoria y acelerar procesamiento)
        y, sr = librosa.load(file_path, duration=30.0, sr=None)
        
        if len(y) == 0:
            print("[IA ANALYZER] Archivo de audio vacío o dañado")
            return resultado

        # 1. Estimar BPM (Tempo)
        print("[IA ANALYZER] Estimando Tempo (BPM)...")
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        if isinstance(tempo, np.ndarray):
            bpm_estimado = float(tempo[0])
        else:
            bpm_estimado = float(tempo)
        
        bpm_estimado = round(bpm_estimado, 2)
        print(f"[IA ANALYZER] BPM Estimado: {bpm_estimado}")

        # 2. Estimar Energía (Raíz cuadrada media - RMS)
        print("[IA ANALYZER] Calculando Energía (RMS)...")
        rms = librosa.feature.rms(y=y)
        energia_promedio = float(np.mean(rms))
        energia_normalizada = min(max(energia_promedio * 2.5, 0.0), 1.0)
        energia_normalizada = round(energia_normalizada, 3)
        print(f"[IA ANALYZER] Energía Promedio: {energia_normalizada}")

        # 3. Estimar Brillo (Spectral Centroid)
        print("[IA ANALYZER] Calculando Brillo Espectral...")
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        brillo_promedio = float(np.mean(spectral_centroids))
        brillo_promedio = round(brillo_promedio, 2)
        print(f"[IA ANALYZER] Brillo Espectral Promedio: {brillo_promedio} Hz")

        # 4. Clasificación de Género y Vector de Timbre (Inferencia de IA Local)
        genero_predicho = 'Desconocido'
        
        # Extraer características para el modelo de ML (MFCCs promedio)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfccs_mean = np.mean(mfccs, axis=1) # 13 características tímbricas
        
        # Excluimos el primer coeficiente MFCC (MFCC 0) que representa la energía/volumen general,
        # de modo que la similitud de timbre no se vea afectada por la amplitud del audio.
        vector_timbre_list = [round(float(val), 4) for val in mfccs_mean[1:]] # 12 descriptores de timbre puro
        
        # Vector de entrada para el modelo
        feature_vector = np.array([[
            bpm_estimado,
            energia_normalizada,
            brillo_promedio,
            *mfccs_mean
        ]])

        if os.path.exists(MODEL_PATH):
            try:
                print("[IA ANALYZER] Cargando modelo clasificador scikit-learn local...")
                model = joblib.load(MODEL_PATH)
                pred = model.predict(feature_vector)
                genero_predicho = str(pred[0])
                print(f"[IA ANALYZER] Inferencia de modelo exitosa. Género: {genero_predicho}")
            except Exception as ml_err:
                print(f"[IA ANALYZER] Error al correr inferencia de modelo scikit-learn: {ml_err}. Usando fallback...")
                genero_predicho = clasificar_heuristico(bpm_estimado, energia_normalizada, brillo_promedio)
        else:
            print("[IA ANALYZER] Modelo scikit-learn local no encontrado. Usando clasificador acústico heurístico...")
            genero_predicho = clasificar_heuristico(bpm_estimado, energia_normalizada, brillo_promedio)

        resultado = {
            'bpm': bpm_estimado,
            'energia': energia_normalizada,
            'brillo': brillo_promedio,
            'genero': genero_predicho,
            'vector_timbre': vector_timbre_list
        }
        
    except Exception as ex:
        print(f"[IA ANALYZER] Error crítico durante el análisis de audio: {ex}")
        
    return resultado

def clasificar_heuristico(bpm, energia, brillo):
    """
    Clasificador heurístico basado en reglas de descriptores de audio reales
    cuando el modelo de Machine Learning no ha sido entrenado.
    """
    # Merengue: Tempo muy rápido (125-145 BPM), energía alta, percusión/trompetas brillantes
    if 125 <= bpm <= 145 and energia > 0.65 and 2000 <= brillo <= 3000:
        return 'Merengue'
    
    # Salsa: Tempo medio/rápido sincopado (90-112 BPM), energía media/alta, metales muy brillantes
    elif 90 <= bpm <= 112 and energia > 0.55 and brillo > 2400:
        return 'Salsa'

    # Reggaeton / Urbano: Ritmo medio (80-108 BPM), energía alta, brillo moderado
    elif 80 <= bpm <= 108 and energia > 0.4 and brillo < 2500:
        return 'Reggaeton / Urbano'
    
    # Electrónica / Dance: Tempo rápido (118-150 BPM), energía alta, brillo alto
    elif 118 <= bpm <= 150 and energia > 0.5 and brillo > 2200:
        return 'Electronic / Dance'
        
    # Rock / Metal: Tempo medio/rápido (100-160 BPM), energía muy alta, brillo muy alto (guitarras distorsionadas)
    elif bpm >= 100 and energia > 0.6 and brillo > 2800:
        return 'Rock / Metal'
        
    # Pop / Indie: Rango de tempo versátil, energía moderada, brillo medio/alto
    elif 90 <= bpm <= 130 and 0.3 <= energia <= 0.65:
        return 'Pop / Indie'
        
    # Balada / Acústica / Clásica: Tempo lento (menos de 90 BPM), baja energía, brillo medio/bajo
    elif bpm < 90 and energia < 0.35:
        return 'Balada / Acústica'
        
    # Jazz / Blues: Tempo medio/lento, energía media, brillo bajo
    elif bpm < 115 and brillo < 1800 and energia < 0.45:
        return 'Jazz / Blues'
        
    else:
        return 'Pop / Alternativo'

def calcular_similitud_coseno(vec1, vec2, bpm1=None, bpm2=None, energia1=None, energia2=None, brillo1=None, brillo2=None):
    """
    Calcula la similitud del coseno centrada en la media (Correlación de Pearson)
    entre dos firmas acústicas (vectores de 12 MFCCs de timbre puro).
    
    Aplica validación cruzada con BPM, energía y brillo para descartar
    falsos positivos entre canciones diferentes.
    """
    # 1. Validación cruzada de ritmo (BPM): Si el tempo difiere en más de 1.0 BPM, no es la misma canción
    if bpm1 is not None and bpm2 is not None:
        if abs(float(bpm1) - float(bpm2)) > 1.0:
            return 0.0
            
    # 2. Validación cruzada de amplitud (Energía): Si la energía difiere en más de un 5% (0.05), no es el mismo tema
    if energia1 is not None and energia2 is not None:
        if abs(float(energia1) - float(energia2)) > 0.05:
            return 0.0
            
    # 3. Validación cruzada de brillo (Spectral Centroid): Si difiere en más de 100 Hz, no es el mismo tema
    if brillo1 is not None and brillo2 is not None:
        if abs(float(brillo1) - float(brillo2)) > 100.0:
            return 0.0

    if not vec1 or not vec2 or len(vec1) == 0 or len(vec2) == 0:
        return 0.0
        
    try:
        # Asegurarse de que tienen la misma longitud (por si hay basura de diferente dimensión en la BD)
        min_len = min(len(vec1), len(vec2))
        v1 = np.array(vec1[:min_len], dtype=float)
        v2 = np.array(vec2[:min_len], dtype=float)
        
        # Centrar los vectores restándoles su media aritmética (Mean Centering)
        v1 = v1 - np.mean(v1)
        v2 = v2 - np.mean(v2)
        
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 == 0.0 or norm_v2 == 0.0:
            return 0.0
            
        dot_product = np.dot(v1, v2)
        similitud = dot_product / (norm_v1 * norm_v2)
        
        # Mapeamos el coeficiente de correlación [-1.0, 1.0] a [0.0, 100.0]
        similitud_porcentaje = float((similitud + 1.0) / 2.0 * 100.0)
        return round(similitud_porcentaje, 2)
    except Exception as e:
        print(f"[IA ANALYZER] Error al calcular similitud de coseno: {e}")
        return 0.0
