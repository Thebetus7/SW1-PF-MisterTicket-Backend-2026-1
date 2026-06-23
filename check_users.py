import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

print("=== LISTADO DE USUARIOS ===")
for u in User.objects.all():
    print(f"Username: {u.username}")
    print(f"Is active: {u.is_active}")
    print(f"Is staff: {u.is_staff}")
    print(f"Password check (fan123): {u.check_password('fan123')}")
    print(f"Password check (artista123): {u.check_password('artista123')}")
    print("------------------------")
