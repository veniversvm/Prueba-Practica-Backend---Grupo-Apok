import random
from django.core.management.base import BaseCommand
from django.db import transaction
from nodes.models import Node

class Command(BaseCommand):
    help = 'Puebla la base de datos con una estructura jerárquica de nodos'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando el sembrado de datos...'))

        # Usamos una transacción atómica para asegurar que se cree todo o nada
        with transaction.atomic():
            # 1. Limpiar datos existentes
            self.stdout.write('Limpiando base de datos...')
            Node.objects.all().delete()

            # 2. Crear Nodos Raíz (Nivel 0)
            roots = []
            root_titles = ["Empresa", "Tecnología", "Recursos", "1", "100"] # Incluimos números
            
            for title in root_titles:
                node = Node.objects.create(title=title, parent=None)
                roots.append(node)
                self.stdout.write(f'Nodo Raíz creado: {title}')

            # 3. Crear Hijos (Nivel 1)
            for root in roots:
                for i in range(1, 4):
                    # Mezclamos palabras y números
                    title = random.choice([f"Sub-{root.title} {i}", str(random.randint(2, 50))])
                    child = Node.objects.create(title=title, parent=root)
                    
                    # 4. Crear Nietos (Nivel 2) para algunos hijos
                    if random.choice([True, False]):
                        for j in range(1, 3):
                            grandchild_title = str(random.randint(51, 999))
                            Node.objects.create(title=grandchild_title, parent=child)

        self.stdout.write(self.style.SUCCESS('¡Seeder ejecutado con éxito! Se ha creado un árbol complejo.'))