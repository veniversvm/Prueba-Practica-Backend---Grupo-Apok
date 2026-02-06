import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class Command(BaseCommand):
    """
    Comando de gestión para configurar el usuario SUDO inicial del sistema.

    Este comando es idempotente:
    1. Si ya existe un usuario con role='SUDO', no hace nada.
    2. Si no existe, lo crea utilizando las credenciales definidas en el entorno (.env).
    """
    help = 'Crea el usuario SUDO inicial únicamente si no existe ninguno en el sistema'

    def handle(self, *args, **options):
        """Ejecuta la lógica de bootstrap del usuario SUDO."""
        
        # 1. Verificación de existencia (Regla de Oro: Solo un SUDO permitido)
        if User.objects.filter(role='SUDO').exists():
            self.stdout.write(self.style.SUCCESS(
                'El sistema ya cuenta con un usuario SUDO. No se realizaron cambios.'
            ))
            return

        # 2. Carga de credenciales desde variables de entorno (.env)
        username = os.environ.get('SUDO_USERNAME')
        email = os.environ.get('SUDO_EMAIL')
        password = os.environ.get('SUDO_PASSWORD')

        if not all([username, email, password]):
            self.stdout.write(self.style.ERROR(
                'ERROR: Faltan variables de entorno requeridas para el SUDO '
                '(.env: SUDO_USERNAME, SUDO_EMAIL o SUDO_PASSWORD).'
            ))
            return

        # 3. Creación del usuario SUDO
        try:
            # Usamos create_superuser para asegurar que tenga acceso a /admin/ de Django
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                role='SUDO',
                is_email_confirmed=True  # Confirmado por defecto para acceso inicial
            )
            self.stdout.write(self.style.SUCCESS(
                f'Usuario SUDO "{username}" creado exitosamente y marcado como confirmado.'
            ))
        except ValidationError as e:
             self.stdout.write(self.style.ERROR(
                f'Error de validación al crear el SUDO: {str(e)}'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Error crítico al crear el usuario SUDO: {str(e)}'
            ))