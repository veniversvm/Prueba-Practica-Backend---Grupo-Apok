# app_nodos/users/management/commands/seed_users.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    """
    Comando de gestión para poblar la base de datos con usuarios de prueba.

    Crea un conjunto de usuarios con diferentes combinaciones de 'role' y
    'is_email_confirmed' para verificar el funcionamiento del Backend de
    Autenticación y el sistema de Permisos.
    """
    help = 'Genera usuarios de prueba con diferentes roles y estados'

    def handle(self, *args, **kwargs):
        """Ejecuta la lógica del seeder."""
        self.stdout.write(self.style.WARNING('Generando usuarios de prueba...'))

        # Lista de usuarios a crear para pruebas granulares (QA/Seguridad)
        test_users = [
            {
                'username': 'admin_boss',
                'email': 'admin@tree.com',
                'role': 'ADMIN',
                'confirmed': True,
                'desc': 'ADMIN confirmado (Puede editar/borrar nodos)'
            },
            {
                'username': 'admin_pending',
                'email': 'pending_admin@tree.com',
                'role': 'ADMIN',
                'confirmed': False,
                'desc': 'ADMIN NO confirmado (Debe fallar login/JWT)'
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
                'desc': 'Usuario NO confirmado (Debe fallar login/JWT)'
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
                # Usa get_or_create para evitar duplicados si el comando se corre varias veces
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
                    user.set_password('password123') # Contraseña genérica para tests
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"Creado: {u_data['username']} - {u_data['desc']}"))
                else:
                    # Si el usuario ya existe, no hacemos nada, manteniendo la configuración de seguridad.
                    self.stdout.write(self.style.NOTICE(f"Saltado: {u_data['username']} ya existe."))

        self.stdout.write(self.style.SUCCESS('¡Seeder de usuarios completado!'))