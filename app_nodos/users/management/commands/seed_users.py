from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Genera usuarios de prueba con diferentes roles y estados'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generando usuarios de prueba...')

        # Lista de usuarios a crear para pruebas granulares
        test_users = [
            {
                'username': 'admin_boss',
                'email': 'admin@tree.com',
                'role': 'ADMIN',
                'confirmed': True,
                'desc': 'ADMIN confirmado (Puede editar/borrar)'
            },
            {
                'username': 'admin_pending',
                'email': 'pending_admin@tree.com',
                'role': 'ADMIN',
                'confirmed': False,
                'desc': 'ADMIN NO confirmado (Debe ser rechazado por el login)'
            },
            {
                'username': 'user_regular',
                'email': 'user@tree.com',
                'role': 'USER',
                'confirmed': True,
                'desc': 'Usuario confirmado (Solo lectura)'
            },
            {
                'username': 'user_new',
                'email': 'new@tree.com',
                'role': 'USER',
                'confirmed': False,
                'desc': 'Usuario NO confirmado (Debe ser rechazado)'
            },
            {
                'username': 'staff_dev',
                'email': 'dev@tree.com',
                'role': 'ADMIN',
                'confirmed': True,
                'desc': 'Segundo ADMIN para pruebas de auditoría'
            },
        ]

        with transaction.atomic():
            for u_data in test_users:
                # Evitamos duplicados si se corre el seeder varias veces
                user, created = User.objects.get_or_create(
                    username=u_data['username'],
                    defaults={
                        'email': u_data['email'],
                        'role': u_data['role'],
                        'is_email_confirmed': u_data['confirmed'],
                        'is_active': True
                    }
                )
                if created:
                    user.set_password('password123') # Password genérico para tests
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"Creado: {u_data['username']} - {u_data['desc']}"))
                else:
                    self.stdout.write(f"Saltado: {u_data['username']} ya existe.")

        self.stdout.write(self.style.SUCCESS('¡Seeder de usuarios completado!'))