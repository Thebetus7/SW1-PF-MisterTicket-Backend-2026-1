import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Intentamos importar firebase_admin para soportar la integración opcional de FCM
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.warning("La librería 'firebase-admin' no está instalada. El backend no podrá transmitir notificaciones push de forma externa. Por favor ejecuta: pip install firebase-admin")


def enviar_push_fcm(usuario, titulo, cuerpo, data_payload=None):
    """
    Envía una notificación push a todos los dispositivos registrados del usuario usando FCM (Firebase Cloud Messaging).
    """
    if data_payload is None:
        data_payload = {}
        
    # Verificar si el usuario desea recibir notificaciones en general
    if not getattr(usuario, 'recibir_notificaciones', True):
        logger.info(f"El usuario {usuario.username} tiene desactivadas las notificaciones.")
        return

    # Buscar los tokens FCM del usuario
    tokens = list(usuario.dispositivos.values_list('fcm_token', flat=True))
    if not tokens:
        logger.info(f"No hay dispositivos (tokens FCM) registrados para el usuario {usuario.username}.")
        return

    # Validar disponibilidad de la librería
    if not FIREBASE_AVAILABLE:
        logger.error("No se puede enviar push: 'firebase-admin' no está instalado. Notificación guardada únicamente en base de datos.")
        return

    # Validar ruta de credenciales en settings
    cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
    if not cred_path:
        # Por defecto buscamos un archivo firebase-credentials.json en la raíz del backend
        base_dir = getattr(settings, 'BASE_DIR', None)
        if base_dir:
            cred_path = os.path.join(base_dir, 'firebase-credentials.json')

    if not cred_path or not os.path.exists(cred_path):
        logger.warning(f"No se encontró el archivo de credenciales de Firebase en '{cred_path}'. La notificación push no será transmitida externamente.")
        return

    # Inicializar Firebase si aún no lo ha sido
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase SDK inicializado exitosamente en el backend.")
        except Exception as e:
            logger.error(f"Error al inicializar Firebase Admin SDK: {e}")
            return

    # Enviar la notificación a cada token del usuario
    data_payload = {k: str(v) for k, v in data_payload.items()}
    data_payload.setdefault('title', titulo)
    data_payload.setdefault('body', cuerpo)

    for token in tokens:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=titulo,
                    body=cuerpo,
                ),
                data=data_payload,
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        channel_id='mister_ticket_push_channel',
                        sound='default',
                        default_sound=True,
                    ),
                ),
            )
            messaging.send(message)
            logger.info(f"Notificación PUSH enviada exitosamente al usuario {usuario.username} al token {token[:15]}...")
        except Exception as e:
            logger.error(f"Error al enviar push a token {token[:15]}...: {e}")
            
            # Limpieza automática de tokens expirados o desinstalados (resiliencia)
            error_str = str(e)
            if "registration-token-not-registered" in error_str or "invalid-registration-token" in error_str:
                logger.info(f"Eliminando token FCM obsoleto/inválido para el usuario {usuario.username}.")
                usuario.dispositivos.filter(fcm_token=token).delete()
