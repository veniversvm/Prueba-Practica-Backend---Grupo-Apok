import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea el usuario SUDO inicial únicamente si no existe ninguno en el sistema'

    def handle(self, *args, **options):
        # 1. Verificación de existencia (Regla de Oro: Solo un SUDO)
        if User.objects.filter(role='SUDO').exists():
            self.stdout.write(self.style.SUCCESS(
                'El sistema ya cuenta con un usuario SUDO. No se realizaron cambios.'
            ))
            return

        # 2. Carga de credenciales desde .env
        username = os.environ.get('SUDO_USERNAME')
        email = os.environ.get('SUDO_EMAIL')
        password = os.environ.get('SUDO_PASSWORD')

        if not all([username, email, password]):
            self.stdout.write(self.style.ERROR(
                'ERROR: Faltan variables de entorno (SUDO_USERNAME, SUDO_EMAIL o SUDO_PASSWORD).'
            ))
            return

        # 3. Creación del usuario
        try:
            # Usamos create_superuser para asegurar que también tenga acceso al /admin/ de Django
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                role='SUDO',
                is_email_confirmed=True # Confirmado por defecto para acceso inicial
            )
            self.stdout.write(self.style.SUCCESS(
                f'Usuario SUDO "{username}" creado exitosamente.'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Error crítico al crear el usuario SUDO: {str(e)}'
            ))