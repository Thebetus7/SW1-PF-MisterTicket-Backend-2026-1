import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from usuarios.models import Artista
from eventos.models import Departamento, GeneroMusical

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea 15 artistas de prueba con usuarios, características, popularidad y foto en null.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('====== INICIANDO SEEDER DE 15 ARTISTAS ======'))

        # 1. Asegurar géneros musicales
        generos_nombres = [
            'Rock', 'Pop', 'Reggaeton', 'Trap', 'Cumbia',
            'Folclore', 'Metal', 'Jazz', 'Salsa', 'Bachata', 'Electro'
        ]
        generos_objetos = []
        for nombre in generos_nombres:
            genero, created = GeneroMusical.objects.get_or_create(nombre=nombre)
            generos_objetos.append(genero)
            if created:
                self.stdout.write(f"Género creado: {nombre}")

        # 2. Asegurar departamentos
        departamentos_nombres = [
            'La Paz', 'Santa Cruz', 'Cochabamba', 
            'Oruro', 'Potosí', 'Tarija', 
            'Chuquisaca', 'Beni', 'Pando'
        ]
        departamentos_objetos = []
        for nombre in departamentos_nombres:
            depto, created = Departamento.objects.get_or_create(nombre=nombre)
            departamentos_objetos.append(depto)
            if created:
                self.stdout.write(f"Departamento creado: {nombre}")

        # 3. Asegurar grupo artista
        grupo_artista, _ = Group.objects.get_or_create(name='artista')

        # 4. Datos de artistas
        artistas_datos = [
            {"nombre": "Los Kjarkas", "bio": "Legendaria agrupación boliviana de música folclórica andina fundada en Capinota."},
            {"nombre": "Octavia", "bio": "Una de las bandas más importantes y representativas del rock pop boliviano."},
            {"nombre": "Chila Jatun", "bio": "Herederos del folclore boliviano, jóvenes músicos con un sonido fresco y tradicional."},
            {"nombre": "Bonny Lovy", "bio": "El productor de la música, cantante boliviano de género urbano y cumbia pop."},
            {"nombre": "Wara", "bio": "Precursores del folk-rock en Bolivia con más de 40 años de trayectoria."},
            {"nombre": "Animal de Ciudad", "bio": "Proyecto de rock alternativo y funk liderado por Ronaldo Vaca Pereira en Santa Cruz."},
            {"nombre": "Efecto Mandarina", "bio": "Banda de jazz fusión contemporánea con un estilo único y voz cautivadora."},
            {"nombre": "Chila Jatun", "bio": "Banda folclórica destacada que representa a la nueva generación de la música andina."},
            {"nombre": "Llegas", "bio": "Famosa agrupación de rock alternativo boliviano formada por Grillo Villegas."},
            {"nombre": "Matamba", "bio": "El máximo exponente del reggae y dread rock en Bolivia."},
            {"nombre": "Kalamarka", "bio": "Grupo de música folclórica que fusiona instrumentos tradicionales con sonidos electrónicos."},
            {"nombre": "Gran Matador", "bio": "Banda paceña de ska, rock y cumbia con un show energético."},
            {"nombre": "Euphoria", "bio": "Reconocida agrupación de cumbia boliviana y música tropical con gran arrastre popular."},
            {"nombre": "Los de Ajayu", "bio": "Grupo folclórico folclore romántico paceño con gran trayectoria nacional."},
            {"nombre": "Ch’ila Jatun", "bio": "Famoso grupo boliviano compuesto por los hijos de los integrantes de Los Kjarkas."}
        ]

        # Evitar nombres repetidos o colisiones si el seeder se ejecuta varias veces
        # Modificamos la lista para asegurarnos de tener 15 únicos
        # Aseguramos nombres únicos añadiendo pequeñas variaciones si es necesario
        nombres_unicos = []
        for i, art in enumerate(artistas_datos):
            nombre = art["nombre"]
            if nombre in nombres_unicos:
                nombre = f"{nombre} Vol. {i}"
            nombres_unicos.append(nombre)
            art["nombre"] = nombre

        for i, art in enumerate(artistas_datos, start=1):
            username = f"artista_seed_{i}"
            email = f"artista_seed_{i}@misterticket.com"
            password = f"artista123"

            # Crear o recuperar usuario
            user, u_created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": art["nombre"].split()[0],
                    "last_name": " ".join(art["nombre"].split()[1:]) if len(art["nombre"].split()) > 1 else ""
                }
            )

            if u_created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Usuario {username} creado."))

            # Asignar grupo
            if grupo_artista not in user.groups.all():
                user.groups.add(grupo_artista)

            # Crear perfil de artista
            popularity = random.randint(30, 99)
            depto = random.choice(departamentos_objetos)

            artista, a_created = Artista.objects.get_or_create(
                usuario=user,
                defaults={
                    "nombre_artistico": art["nombre"],
                    "biografia": art["bio"],
                    "foto": None,
                    "departamento_origen": depto,
                    "popularidad": popularity
                }
            )

            if a_created:
                # Asignar géneros aleatorios (entre 1 y 2)
                generos_seleccionados = random.sample(generos_objetos, random.randint(1, 2))
                artista.generos_musicales.set(generos_seleccionados)
                self.stdout.write(self.style.SUCCESS(
                    f"Artista '{artista.nombre_artistico}' creado (Popularidad: {popularity}, Origen: {depto.nombre})"
                ))
            else:
                # Si ya existe, actualizamos popularidad y origen para pruebas
                artista.popularidad = popularity
                artista.departamento_origen = depto
                artista.save()
                self.stdout.write(self.style.WARNING(
                    f"Artista '{artista.nombre_artistico}' ya existía, actualizado (Popularidad: {popularity}, Origen: {depto.nombre})"
                ))

        self.stdout.write(self.style.SUCCESS('====== SEED DE 15 ARTISTAS COMPLETADO ====== \n'))
