import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import sys

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Para que Django detecte las apps dentro de la carpeta "apps"
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-misterticket-secret-key-default-dev')
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 3rd party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'storages',

    # Local apps
    'usuarios',
    'eventos',
    'tickets',
    'pagos',
    'musica',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'core.urls'
AUTH_USER_MODEL = 'usuarios.Usuario'  # Custom user model para manejar roles

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'prueba',
        'USER': 'neondb_owner',
        'PASSWORD': 'npg_csKG9yDXOaB0',
        'HOST': 'ep-shy-wind-acg84pj4.sa-east-1.aws.neon.tech',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/La_Paz'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django 5: usar STORAGES (STATICFILES_STORAGE y STORAGES son mutuamente excluyentes)
_STATICFILES_BACKEND = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# =============================================================================
# STORAGE — MinIO (local) / AWS S3 (producción)
# Controla con la variable USE_S3 en el archivo .env
# =============================================================================
USE_S3 = os.getenv('USE_S3', 'False') == 'True'

if USE_S3:
    # Credenciales y configuración del bucket
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', 'misterticket')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')

    # Para MinIO local — se omite en producción con AWS S3 real
    AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL', '')

    # MinIO no soporta ACLs por defecto, así que no establecemos ACL
    # Si usas AWS S3 en producción, descomenta la siguiente línea:
    # AWS_DEFAULT_ACL = 'public-read'
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False

    # Desactivar SSL si el endpoint es http:// (MinIO local)
    if AWS_S3_ENDPOINT_URL and AWS_S3_ENDPOINT_URL.startswith('http://'):
        AWS_S3_USE_SSL = False
        AWS_S3_URL_PROTOCOL = 'http:'
    else:
        AWS_S3_USE_SSL = True
        AWS_S3_URL_PROTOCOL = 'https:'

    # URL pública de los archivos
    if AWS_S3_ENDPOINT_URL:
        # MinIO: la URL pública usa el endpoint local
        AWS_S3_CUSTOM_DOMAIN = f'{AWS_S3_ENDPOINT_URL.replace("http://", "").replace("https://", "")}/{AWS_STORAGE_BUCKET_NAME}'
        MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/'
    else:
        # AWS S3 real en producción
        AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
        MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
        },
        'staticfiles': {
            'BACKEND': _STATICFILES_BACKEND,
        },
    }

    print(f'[STORAGE] >> Usando MinIO/S3 -> Bucket: {AWS_STORAGE_BUCKET_NAME} | Endpoint: {AWS_S3_ENDPOINT_URL}')
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
            'OPTIONS': {
                'location': MEDIA_ROOT,
                'base_url': MEDIA_URL,
            },
        },
        'staticfiles': {
            'BACKEND': _STATICFILES_BACKEND,
        },
    }

    print(f'[STORAGE] >> Usando almacenamiento LOCAL -> {MEDIA_ROOT}')

# Rest Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CORS_ALLOW_ALL_ORIGINS = True  # Cambiar en producción a la URL de tu Next.js

# Stripe Configuration (legado — ya no se usa activamente)
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')

# ── Libélula Payment Gateway ─────────────────────────────────────────────────
# API key de Libélula (se envía en cada payload de registro de deuda)
LIBELULA_API_KEY = os.getenv('LIBELULA_API_KEY', 'xOvVur3LHQx7zHknwD2YOp4gS1Rr9U1PZ')

# URL base pública del backend (sin slash final).
# Desarrollo: URL de ngrok  →  https://xxxx.ngrok.io
# Producción: https://api.misterticket.com
BACKEND_BASE_URL = os.getenv('BACKEND_BASE_URL', 'http://localhost:8000')

