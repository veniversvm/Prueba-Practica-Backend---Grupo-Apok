# nodes/management/commands/seed_nodes.py
import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from nodes.models import Node
from num2words import num2words
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Puebla la base de datos con una estructura jerárquica de nodos'

    def handle(self, *args, **kwargs):
        self.stdout.write(
            self.style.WARNING('Iniciando el sembrado de datos para el nuevo modelo...')
        )

        # Obtener el usuario SUDO (ID 1)
        try:
            sudo_user = User.objects.get(id=1)
            self.stdout.write(f'✅ Usando SUDO user: {sudo_user.username} (ID: {sudo_user.id})')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                '❌ No existe el usuario con ID 1. Crea un usuario SUDO primero.'
            ))
            return

        with transaction.atomic():
            # Limpiar datos existentes
            self.stdout.write('Limpiando base de datos de nodos...')
            Node.objects.all().delete()

            # Contenidos disponibles
            root_contents = [
                "Empresa Principal",
                "Departamento de Tecnología", 
                "Recursos Humanos",
                "Finanzas Corporativas",
                "Proyectos Activos",
                "Operaciones",
                "Marketing",
                "Ventas",
                "Soporte Técnico",
                "Investigación y Desarrollo"
            ]
            
            child_contents = [
                "Subdivisión",
                "Equipo",
                "Proyecto",
                "Departamento",
                "Grupo de Trabajo",
                "Comité",
                "Iniciativa",
                "Programa"
            ]
            
            task_contents = [
                "Tarea",
                "Subtarea",
                "Documentación",
                "Revisión",
                "Implementación",
                "Pruebas",
                "Despliegue",
                "Mantenimiento"
            ]
            
            detail_contents = [
                "Checklist",
                "Nota",
                "Comentario",
                "Observación",
                "Recordatorio",
                "Seguimiento",
                "Actualización",
                "Corrección"
            ]

            # 1. Crear Nodos Raíz (Nivel 0)
            roots = []
            for i, content in enumerate(root_contents[:7]):
                node = Node.objects.create(
                    content=f"{content} #{i+1}",
                    parent=None,
                    created_by=sudo_user  # ← ASIGNAR SUDO USER
                )
                roots.append(node)
                
                try:
                    title = num2words(node.id, lang='es')
                except:
                    title = num2words(node.id, lang='en')
                    
                self.stdout.write(f'Nodo Raíz creado: ID={node.id}, Content="{node.content}"')

            # 2. Crear Hijos (Nivel 1)
            child_nodes = []
            for root_idx, root in enumerate(roots):
                for i in range(1, random.randint(2, 4)):
                    child_type = random.choice(child_contents)
                    child_content = f"{child_type} {chr(64+i)} de {root.content}"
                    
                    child = Node.objects.create(
                        content=child_content,
                        parent=root,
                        created_by=sudo_user  # ← ASIGNAR SUDO USER
                    )
                    child_nodes.append(child)
                    
                    self.stdout.write(f'  ├─ Hijo creado: ID={child.id}, Content="{child_content}"')

                    # 3. Crear Nietos (Nivel 2) - 60% de probabilidad
                    if random.random() < 0.6:
                        for j in range(1, random.randint(2, 4)):
                            task_type = random.choice(task_contents)
                            unique_id = str(uuid.uuid4())[:8]
                            grandchild_content = f"{task_type} {j}.{i} - {unique_id}"
                            
                            grandchild = Node.objects.create(
                                content=grandchild_content,
                                parent=child,
                                created_by=sudo_user  # ← ASIGNAR SUDO USER
                            )
                            
                            self.stdout.write(f'  │   └─ Nieto creado: ID={grandchild.id}, Content="{grandchild_content}"')

                            # 4. Crear Bisnietos (Nivel 3) - 30% de probabilidad
                            if random.random() < 0.3:
                                for k in range(1, random.randint(2, 3)):
                                    detail_type = random.choice(detail_contents)
                                    detail_unique_id = str(uuid.uuid4())[:6]
                                    great_grandchild_content = f"{detail_type} {k}.{j}.{i} - {detail_unique_id}"
                                    
                                    Node.objects.create(
                                        content=great_grandchild_content,
                                        parent=grandchild,
                                        created_by=sudo_user  # ← ASIGNAR SUDO USER
                                    )
                                    self.stdout.write(f'  │       └─ Bisnieto creado: Content="{great_grandchild_content}"')

            # 5. Crear algunos nodos hoja únicos
            self.stdout.write('\nCreando nodos hoja adicionales...')
            for i in range(5):
                leaf_unique_id = str(uuid.uuid4())[:8]
                leaf_content = f"Nodo Independiente #{i+1} - {leaf_unique_id}"
                
                Node.objects.create(
                    content=leaf_content,
                    parent=random.choice(roots) if random.choice([True, False]) else None,
                    created_by=sudo_user  # ← ASIGNAR SUDO USER
                )
                self.stdout.write(f'Nodo hoja creado: "{leaf_content}"')

            # 6. Crear algunos nodos con números
            self.stdout.write('\nCreando nodos con contenido numérico...')
            for i in range(3):
                numeric_content = str(random.randint(1000, 99999))
                Node.objects.create(
                    content=f"Número {numeric_content}",
                    parent=random.choice(roots) if i % 2 == 0 else None,
                    created_by=sudo_user  # ← ASIGNAR SUDO USER
                )
                self.stdout.write(f'Nodo numérico creado: "{numeric_content}"')

            # 7. Estadísticas finales
            total_nodes = Node.objects.count()
            root_count = Node.objects.filter(parent__isnull=True).count()
            leaf_count = Node.objects.filter(children__isnull=True).count()
            
            self.stdout.write('\n' + '='*50)
            self.stdout.write(self.style.SUCCESS('¡Seeder de nodos completado exitosamente!'))
            self.stdout.write(f'Total de nodos creados: {total_nodes}')
            self.stdout.write(f'Nodos raíz: {root_count}')
            self.stdout.write(f'Nodos hoja: {leaf_count}')
            self.stdout.write(f'Creados por: {sudo_user.username} (ID: {sudo_user.id})')
            self.stdout.write('='*50)