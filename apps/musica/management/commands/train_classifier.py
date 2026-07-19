import os
import numpy as np
import joblib
from django.core.management.base import BaseCommand
from django.conf import settings
from sklearn.ensemble import RandomForestClassifier

class Command(BaseCommand):
    help = 'Entrena y guarda un clasificador de géneros musicales local en base a características acústicas'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Iniciando el entrenamiento del clasificador de música local por IA..."))
        
        # 1. Crear el directorio de destino si no existe
        model_dir = os.path.join(settings.BASE_DIR, 'core', 'ia_models')
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, 'genero_classifier.joblib')

        # 2. Generar un dataset sintético representativo pero con bases físicas reales
        # Características: [BPM, Energia, Brillo, MFCC_1, MFCC_2, ..., MFCC_13] -> Total 16 variables
        generos = ['Reggaeton / Urbano', 'Electronic / Dance', 'Rock / Metal', 'Pop / Indie', 'Balada / Acústica', 'Jazz / Blues', 'Merengue', 'Salsa']
        
        X = []
        y = []
        
        np.random.seed(42) # Semilla para reproducibilidad
        
        # Generar 500 muestras por cada género con distribuciones realistas
        for gen in generos:
            for _ in range(500):
                if gen == 'Reggaeton / Urbano':
                    # Ritmo regular (90-100 BPM), alta energía, brillo moderado
                    bpm = np.random.normal(95, 5)
                    energia = np.random.normal(0.75, 0.08)
                    brillo = np.random.normal(1600, 300)
                    mfcc = np.random.normal([12, 5, -8, 2, -1, 3, -4, 1, -2, 2, -3, 1, -1], 2)
                elif gen == 'Electronic / Dance':
                    # Ritmo rápido (128 BPM), energía muy alta, brillo alto
                    bpm = np.random.normal(128, 4)
                    energia = np.random.normal(0.85, 0.05)
                    brillo = np.random.normal(2600, 400)
                    mfcc = np.random.normal([15, 8, -5, 4, 1, 5, -2, 3, 0, 4, -1, 3, 1], 2)
                elif gen == 'Rock / Metal':
                    # Ritmo rápido/medio (110-150 BPM), energía extrema, brillo muy alto
                    bpm = np.random.normal(130, 15)
                    energia = np.random.normal(0.90, 0.06)
                    brillo = np.random.normal(3200, 500)
                    mfcc = np.random.normal([18, 10, -2, 6, 3, 7, 0, 5, 2, 6, 1, 5, 3], 2)
                elif gen == 'Pop / Indie':
                    # Características promedio (100-115 BPM), energía media, brillo medio/alto
                    bpm = np.random.normal(110, 10)
                    energia = np.random.normal(0.55, 0.10)
                    brillo = np.random.normal(2100, 350)
                    mfcc = np.random.normal([10, 3, -10, 1, -3, 2, -5, 0, -3, 1, -4, 0, -2], 2)
                elif gen == 'Balada / Acústica':
                    # Lento (70-85 BPM), baja energía, brillo bajo/medio
                    bpm = np.random.normal(78, 6)
                    energia = np.random.normal(0.28, 0.07)
                    brillo = np.random.normal(1200, 250)
                    mfcc = np.random.normal([5, -2, -15, -3, -6, -1, -8, -2, -5, -1, -6, -2, -4], 2)
                elif gen == 'Merengue':
                    # Ritmo tropical muy rápido (130-145 BPM), energía alta, percusión brillante
                    bpm = np.random.normal(135, 6)
                    energia = np.random.normal(0.80, 0.07)
                    brillo = np.random.normal(2500, 350)
                    mfcc = np.random.normal([14, 6, -6, 3, -2, 4, -3, 2, -1, 3, -2, 2, 0], 2)
                elif gen == 'Salsa':
                    # Ritmo rápido sincopado (90-105 BPM de clave), energía alta, metales muy brillantes
                    bpm = np.random.normal(98, 5)
                    energia = np.random.normal(0.70, 0.08)
                    brillo = np.random.normal(2800, 400)
                    mfcc = np.random.normal([13, 7, -7, 4, -3, 5, -4, 3, -2, 4, -3, 3, 1], 2)
                else: # Jazz / Blues
                    # Lento/Medio (80-110 BPM), energía baja/media, brillo bajo (cálido)
                    bpm = np.random.normal(92, 12)
                    energia = np.random.normal(0.38, 0.08)
                    brillo = np.random.normal(1400, 300)
                    mfcc = np.random.normal([8, 1, -12, 0, -5, 1, -6, -1, -4, 0, -5, -1, -3], 2)
                
                # Asegurar rangos correctos
                energia = min(max(energia, 0.0), 1.0)
                brillo = max(brillo, 100.0)
                
                features = [bpm, energia, brillo] + list(mfcc)
                X.append(features)
                y.append(gen)
        
        X = np.array(X)
        y = np.array(y)
        
        # 3. Entrenar el clasificador RandomForest
        self.stdout.write("Entrenando modelo RandomForestClassifier localmente...")
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Evaluar la precisión sobre el mismo dataset para validación
        precision = model.score(X, y)
        self.stdout.write(self.style.SUCCESS(f"Entrenamiento completado. Precisión sobre dataset de entrenamiento: {precision * 100:.2f}%"))
        
        # 4. Guardar el modelo entrenado con joblib
        joblib.dump(model, model_path)
        self.stdout.write(self.style.SUCCESS(f"Modelo guardado exitosamente en: {model_path}"))
        self.stdout.write(self.style.SUCCESS("¡Clasificador de IA local listo para producción offline!"))
