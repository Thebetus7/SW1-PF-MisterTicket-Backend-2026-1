from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import os


class Command(BaseCommand):
    help = 'Crea el superusuario admin y usuarios de prueba con roles (fan, artista, verificador).'

    def _create_or_update_superuser(self, User, username, email, password):
        """Crea o actualiza el superusuario admin."""
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"El usuario '{username}' ya existe."))
            user = User.objects.get(username=username)
            if not user.is_superuser:
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f"El usuario '{username}' ahora es superusuario."))
        else:
            self.stdout.write(self.style.NOTICE(f"Creando superusuario '{username}'..."))
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(
                f"Superusuario '{username}' creado exitosamente con contraseña '{password}'."
            ))

    def _create_user_with_role(self, User, username, email, password, role_name):
        """Crea un usuario normal y le asigna un rol (Group) y perfil correspondiente."""
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"El usuario '{username}' ya existe."))
            user = User.objects.get(username=username)
        else:
            self.stdout.write(self.style.NOTICE(f"Creando usuario '{username}'..."))
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(
                f"Usuario '{username}' creado con contraseña '{password}'."
            ))

        # Asignar rol
        try:
            grupo = Group.objects.get(name=role_name)
            if not user.groups.filter(name=role_name).exists():
                user.groups.add(grupo)
                self.stdout.write(self.style.SUCCESS(
                    f"  -> Rol '{role_name}' asignado a '{username}'."
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"  -> '{username}' ya tiene el rol '{role_name}'."
                ))
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f"  [x] El rol '{role_name}' no existe. Ejecuta 'migrate' primero."
            ))
            return

        # Crear perfil según el rol si no existe
        if role_name == 'artista':
            from usuarios.models import Artista
            artista, created = Artista.objects.get_or_create(
                usuario=user,
                defaults={'nombre_artistico': f"Artista {username.capitalize()}"}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"  -> Perfil de Artista '{artista.nombre_artistico}' creado para '{username}'."
                ))
        elif role_name == 'verificador':
            from usuarios.models import Verificador, Promotor
            promotor_username = 'promotor2' if username == 'verificador2' else 'promotor1'
            promotor = Promotor.objects.filter(usuario__username=promotor_username).first()
            if not promotor:
                self.stdout.write(self.style.ERROR(
                    f"  [x] No se encontró {promotor_username} para asignar a '{username}'."
                ))
                return
            verificador, created = Verificador.objects.get_or_create(
                usuario=user,
                defaults={'pago': 50.00, 'estado': 'activo', 'promotor': promotor}
            )
            if created or verificador.promotor_id != promotor.id:
                verificador.promotor = promotor
                verificador.save(update_fields=['promotor'])
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"  -> Perfil de Verificador creado para '{username}' (promotor: {promotor.razon_social})."
                ))
        elif role_name == 'promotor':
            from usuarios.models import Promotor
            promotor, created = Promotor.objects.get_or_create(
                usuario=user,
                defaults={
                    'razon_social': f"Promotor {username.capitalize()}",
                    'nit_rfc': f"NIT-{username.upper()}-123",
                    'banco_nombre': "Banco de la Nación",
                    'cuenta_bancaria': "123-456789-00"
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"  -> Perfil de Promotor '{promotor.razon_social}' creado para '{username}'."
                ))

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # --- 1. SUPERUSUARIO ADMIN ---
        self.stdout.write(self.style.HTTP_INFO('\n====== CREANDO SUPERUSUARIO ======'))
        admin_username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@misterticket.com')
        admin_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
        self._create_or_update_superuser(User, admin_username, admin_email, admin_password)

        # --- 2. USUARIOS DE PRUEBA CON ROLES ---
        self.stdout.write(self.style.HTTP_INFO('\n====== CREANDO USUARIOS DE PRUEBA ======'))

        usuarios_prueba = [
            ('fan1', 'fan1@misterticket.com', 'fan12345', 'fan'),
            ('fan2', 'fan2@misterticket.com', 'fan12345', 'fan'),
            ('artista1', 'artista1@misterticket.com', 'artista12345', 'artista'),
            ('artista2', 'artista2@misterticket.com', 'artista12345', 'artista'),
            ('promotor1', 'promotor1@misterticket.com', 'promotor123', 'promotor'),
            ('promotor2', 'promotor2@misterticket.com', 'promotor123', 'promotor'),
            ('verificador1', 'verificador1@misterticket.com', 'verificador12345', 'verificador'),
            ('verificador2', 'verificador2@misterticket.com', 'verificador12345', 'verificador'),
        ]

        for username, email, password, role in usuarios_prueba:
            self._stdout_separator()
            self._create_user_with_role(User, username, email, password, role)

        self.stdout.write(self.style.HTTP_INFO('\n====== SEED COMPLETADO ======\n'))

    def _stdout_separator(self):
        self.stdout.write('-' * 40)
