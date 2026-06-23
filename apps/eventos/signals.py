import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Evento
from usuarios.models import Notificacion, SeguidorPromotor
from usuarios.utils.firebase_helper import enviar_push_fcm

logger = logging.getLogger(__name__)
Usuario = get_user_model()


@receiver(post_save, sender=Evento)
def notificar_publicacion_evento(sender, instance, created, **kwargs):
    """
    Señal post_save para Evento. 
    Cuando el estado de un evento es 'publicado', crea y envía notificaciones:
    1. A los fans que siguen al promotor del evento.
    2. A los artistas incluidos en el elenco del evento.
    """
    if instance.estado != 'publicado':
        return

    # ──── 1. NOTIFICACIÓN A FANS SEGUIDORES ────
    # Evitar duplicidad: Si ya existe alguna notificación 'nuevo_evento' para este evento,
    # significa que ya fue publicado previamente.
    ya_notificado_fans = Notificacion.objects.filter(
        evento=instance, 
        tipo='nuevo_evento'
    ).exists()

    if not ya_notificado_fans:
        logger.info(f"Procesando notificaciones para seguidores del promotor: {instance.promotor.razon_social}")
        
        # Obtener los usuarios que siguen a este promotor
        seguidores = SeguidorPromotor.objects.filter(promotor=instance.promotor).select_related('usuario')
        
        titulo_fan = "¡Nuevo Evento Publicado! 🎉"
        cuerpo_fan = f"El promotor {instance.promotor.razon_social} ha publicado un nuevo evento: {instance.nombre}."
        payload_fan = {
            'evento_id': str(instance.id),
            'tipo': 'nuevo_evento'
        }

        notificaciones_a_crear = []
        usuarios_a_enviar_push = []

        for seguidor in seguidores:
            usuario = seguidor.usuario
            if getattr(usuario, 'recibir_notificaciones', True):
                # Crear objeto de notificación en BD
                notificaciones_a_crear.append(Notificacion(
                    usuario=usuario,
                    titulo=titulo_fan,
                    mensaje=cuerpo_fan,
                    tipo='nuevo_evento',
                    evento=instance
                ))
                usuarios_a_enviar_push.append(usuario)

        # Creación en bulk en base de datos para optimizar rendimiento
        if notificaciones_a_crear:
            Notificacion.objects.bulk_create(notificaciones_a_crear)
            
            # Enviar push FCM a cada uno
            for usuario in usuarios_a_enviar_push:
                enviar_push_fcm(usuario, titulo_fan, cuerpo_fan, payload_fan)

    # ──── 2. NOTIFICACIÓN A ARTISTAS DEL ELENCO ────
    # Obtener todas las presentaciones asociadas a este evento
    presentaciones = instance.presentaciones.select_related('artista__usuario').all()
    
    titulo_artista = "¡Has sido presentado en un nuevo evento! 🎤"
    cuerpo_artista = f"Has sido incluido en el elenco del evento '{instance.nombre}' organizado por {instance.promotor.razon_social}."
    payload_artista = {
        'evento_id': str(instance.id),
        'tipo': 'evento_artista'
    }

    for pres in presentaciones:
        artista = pres.artista
        # Comprobar si el artista tiene un usuario vinculado en el sistema
        if artista.usuario:
            usuario_artista = artista.usuario
            
            # Evitar duplicidad para este artista en particular
            ya_notificado_artista = Notificacion.objects.filter(
                usuario=usuario_artista,
                evento=instance,
                tipo='evento_artista'
            ).exists()

            if not ya_notificado_artista and getattr(usuario_artista, 'recibir_notificaciones', True):
                # Guardar notificación en BD
                Notificacion.objects.create(
                    usuario=usuario_artista,
                    titulo=titulo_artista,
                    mensaje=cuerpo_artista,
                    tipo='evento_artista',
                    evento=instance
                )
                # Enviar push FCM
                enviar_push_fcm(usuario_artista, titulo_artista, cuerpo_artista, payload_artista)
