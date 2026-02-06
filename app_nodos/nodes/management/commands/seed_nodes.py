import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from nodes.models import Node

User = get_user_model()

class Command(BaseCommand):
    """
    Comando de gestión personalizado para poblar la base de datos con
    una estructura jerárquica de nodos.

    Asegura que cada nodo creado contenga campos de auditoría ('created_by' y
    'updated_by') asignados a usuarios con roles ADMIN o SUDO.
    """
    help = 'Puebla la base de datos con una estructura jerárquica de nodos y auditoría'

    def handle(self, *args, **kwargs):
        self.stdout.write(
            self.style.WARNING('Iniciando el sembrado de datos con auditoría...')
        )

        # 1. Obtener usuarios capaces de crear nodos (ADMIN y SUDO confirmados)
        admins = list(
            User.objects.filter(role__in=['ADMIN', 'SUDO'], is_email_confirmed=True)
        )
        
        if not admins:
            self.stdout.write(self.style.ERROR(
                'No hay usuarios ADMIN o SUDO confirmados. Ejecuta setup_sudo y seed_users primero.'
            ))
            return

        with transaction.atomic():
            # 2. Limpiar datos existentes
            self.stdout.write('Limpiando base de datos de nodos...')
            Node.objects.all().delete()

            # 3. Crear Nodos Raíz (Nivel 0)
            roots = []
            root_titles = ["Empresa", "Tecnología", "Recursos", "1", "100"]
            
            for title in root_titles:
                author = random.choice(admins)  # Seleccionamos un autor al azar
                node = Node.objects.create(
                    title=title, 
                    parent=None,
                    created_by=author,
                    updated_by=author
                )
                roots.append(node)
                self.stdout.write(f'Nodo Raíz creado: {title} (por {author.username})')

            # 4. Crear Hijos (Nivel 1)
            for root in roots:
                for i in range(1, 4):
                    author = random.choice(admins)
                    # El título incluye números para probar la conversión
                    title = random.choice([f"Sub-{root.title} {i}", str(random.randint(2, 50))])
                    
                    child = Node.objects.create(
                        title=title, 
                        parent=root,
                        created_by=author,
                        updated_by=author
                    )
                    
                    # 5. Crear Nietos (Nivel 2) para el 50% de los hijos
                    if random.choice([True, False]):
                        for j in range(1, 3):
                            author = random.choice(admins)
                            grandchild_title = str(random.randint(51, 999))
                            
                            Node.objects.create(
                                title=grandchild_title, 
                                parent=child,
                                created_by=author,
                                updated_by=author
                            )

        self.stdout.write(
            self.style.SUCCESS('¡Seeder de nodos completado con auditoría exitosa!')
        )