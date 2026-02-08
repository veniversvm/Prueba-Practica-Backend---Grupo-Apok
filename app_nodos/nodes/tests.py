# nodes/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from nodes.models import Node
from nodes.serializers import NodeSerializer
from django.shortcuts import get_object_or_404  

User = get_user_model()


# nodes/tests.py - Tests corregidos
class NodeSerializerTest(TestCase):
    """
    Suite de pruebas para validar la lógica de negocio y la serialización.
    """
    def setUp(self):
        """Configuración de la estructura base del árbol para pruebas."""
        self.root_node = Node.objects.create(content="Raíz")
        self.child_node = Node.objects.create(content="Hijo", parent=self.root_node)
        self.grandchild_node = Node.objects.create(content="Nieto", parent=self.child_node)

    # --- TESTS DE GET (Serialización / Depth) ---

    def test_title_generation_spanish(self):
        """Valida que el título se genere correctamente en español."""
        context = {'language': 'es', 'current_depth': 0, 'depth': None}
        serializer = NodeSerializer(self.root_node, context=context)
        
        title = serializer.data['title']
        self.assertIsInstance(title, str)
        self.assertTrue(len(title) > 0)

    def test_title_generation_english(self):
        """Valida que el título se genere correctamente en inglés."""
        context = {'language': 'en', 'current_depth': 0, 'depth': None}
        serializer = NodeSerializer(self.root_node, context=context)
        
        title = serializer.data['title']
        self.assertIsInstance(title, str)
        self.assertTrue(len(title) > 0)

    def test_serialization_depth_zero(self):
        """Valida que con depth=0 solo se retorne la raíz (sin hijos)."""
        context = {'depth': 0, 'current_depth': 0}
        serializer = NodeSerializer(self.root_node, context=context)
        
        self.assertEqual(len(serializer.data['children']), 0)

    def test_serialization_depth_one(self):
        """Valida que con depth=1 se retorne el primer nivel de hijos, pero no el segundo."""
        context = {'depth': 1, 'current_depth': 0}
        serializer = NodeSerializer(self.root_node, context=context)
        
        # Debe tener 1 hijo directo
        self.assertEqual(len(serializer.data['children']), 1)
        # El hijo directo NO debe tener hijos (depth=1 alcanza hasta aquí)
        self.assertEqual(len(serializer.data['children'][0]['children']), 0)

    def test_serialization_depth_two(self):
        """Valida que con depth=2 se retorne la jerarquía completa."""
        context = {'depth': 2, 'current_depth': 0}
        serializer = NodeSerializer(self.root_node, context=context)
        
        # Verificamos que el nieto exista
        hijo = serializer.data['children'][0]
        self.assertTrue(len(hijo['children']) > 0)
        # El nieto NO debe tener hijos (depth=2 alcanza hasta aquí)
        self.assertEqual(len(hijo['children'][0]['children']), 0)

    def test_serialization_default_depth(self):
        """Valida que sin especificar depth solo muestre hijos directos."""
        context = {'depth': None, 'current_depth': 0}
        serializer = NodeSerializer(self.root_node, context=context)
        
        # Debe mostrar hijos directos
        self.assertEqual(len(serializer.data['children']), 1)
        # Los hijos NO deben mostrar sus hijos (solo un nivel)
        hijo = serializer.data['children'][0]
        self.assertEqual(len(hijo['children']), 0)

    def test_serialization_depth_infinite(self):
        """Valida que con depth=-1 muestre todos los niveles."""
        context = {'depth': -1, 'current_depth': 0}
        serializer = NodeSerializer(self.root_node, context=context)
        
        # Debe mostrar todos los niveles
        self.assertEqual(len(serializer.data['children']), 1)
        hijo = serializer.data['children'][0]
        self.assertTrue(len(hijo['children']) > 0)
        # Si hay más niveles, también deberían mostrarse
        # (aunque en nuestro caso solo tenemos 3 niveles)

    def test_created_at_timezone_conversion(self):
        """Valida que created_at se convierta a la zona horaria solicitada."""
        context = {'user_timezone': 'America/New_York', 'current_depth': 0, 'depth': None}
        serializer = NodeSerializer(self.root_node, context=context)
        
        created_at = serializer.data['created_at']
        self.assertIsInstance(created_at, str)
        # Debe tener formato YYYY-MM-DD HH:MM:SS
        self.assertRegex(created_at, r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')

    def test_created_at_fallback_to_utc(self):
        """Valida que created_at haga fallback a UTC si la zona horaria es inválida."""
        context = {'user_timezone': 'Zona/Invalida', 'current_depth': 0, 'depth': None}
        serializer = NodeSerializer(self.root_node, context=context)
        
        created_at = serializer.data['created_at']
        self.assertIsInstance(created_at, str)
        # Debe contener UTC al final como fallback
        self.assertIn('UTC', created_at)

class NodeAPITest(APITestCase):
    """
    Suite de pruebas para validar los endpoints de la API, incluyendo:
    - Autenticación
    - Lógica de Borrado Lógico (Soft Delete)
    - Validación de ID (>= 1)
    - Internacionalización
    """
    def setUp(self):
        """Configuración de usuario con permisos y estructura de árbol."""
        # 1. CREAR Y AUTENTICAR AL USUARIO
        self.admin_user = User.objects.create_user(
            username='testadmin', 
            email='admin@test.com', 
            password='testpassword',
            role='ADMIN',
            is_email_confirmed=True
        )
        # 2. Loguear al cliente de prueba
        self.client.force_authenticate(user=self.admin_user)

        # 3. Crear un árbol: Padre -> Hijo
        self.parent = Node.objects.create(content="Padre_API")
        self.child = Node.objects.create(content="Hijo_API", parent=self.parent)
        
        self.parent_url = reverse('node-detail', kwargs={'pk': self.parent.pk})
        self.child_url = reverse('node-detail', kwargs={'pk': self.child.pk})
        self.nodes_list_url = reverse('node-list')

    # --- TESTS DE ID VALIDATION (>= 1) ---

    def test_get_node_with_id_zero(self):
        """Valida que no se pueda acceder a un nodo con ID 0."""
        url = reverse('node-detail', kwargs={'pk': 0})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("El ID debe ser un número positivo mayor o igual a 1.", response.data['error'])

    def test_get_node_with_negative_id(self):
        """Valida que no se pueda acceder a un nodo con ID negativo."""
        url = reverse('node-detail', kwargs={'pk': -5})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("El ID debe ser un número positivo mayor o igual a 1.", response.data['error'])

    def test_get_node_with_invalid_id_format(self):
        """Valida que no se pueda acceder a un nodo con ID no numérico."""
        url = reverse('node-detail', kwargs={'pk': 'abc'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ID inválido. Debe ser un número entero.", response.data['error'])

    def test_get_node_with_valid_id(self):
        """Valida que se pueda acceder a un nodo con ID válido."""
        response = self.client.get(self.parent_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- TESTS DE SOFT DELETE ---

    def test_delete_leaf_node_success(self):
        """Valida que borrar un nodo hoja resulte en 200 y soft delete."""
        response = self.client.delete(self.child_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], f"Nodo {self.child.id} eliminado exitosamente.")
        
        # Verifica que solo queda 1 nodo no borrado lógicamente (el padre)
        self.assertEqual(Node.objects.filter(is_deleted=False).count(), 1)
        self.assertTrue(Node.objects.filter(is_deleted=True, pk=self.child.pk).exists())

    def test_delete_parent_node_fails(self):
        """Valida que borrar un nodo con hijos activos resulte en 400."""
        response = self.client.delete(self.parent_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No se puede eliminar un nodo que tiene hijos activos.", response.data['error'])
        self.assertEqual(response.data['code'], "has_children")
        
        # Verifica que el nodo padre NO se haya borrado
        self.assertFalse(Node.objects.get(pk=self.parent.pk).is_deleted)

    def test_list_excludes_deleted_nodes(self):
        """Valida que los nodos borrados lógicamente no aparezcan en el listado."""
        # Borrar el hijo
        self.child.soft_delete()
        
        response = self.client.get(self.nodes_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # El padre debería aparecer sin hijos
        parent_data = response.data[0]
        self.assertEqual(len(parent_data['children']), 0)

    # --- TESTS DE INTERNATIONALIZATION ---

    def test_list_with_spanish_language(self):
        """Valida que los títulos se generen en español con header Accept-Language: es."""
        headers = {'HTTP_ACCEPT_LANGUAGE': 'es'}
        response = self.client.get(self.nodes_list_url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verificar que el título está presente
        self.assertIn('title', response.data[0])

    def test_list_with_english_language(self):
        """Valida que los títulos se generen en inglés con header Accept-Language: en."""
        headers = {'HTTP_ACCEPT_LANGUAGE': 'en'}
        response = self.client.get(self.nodes_list_url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('title', response.data[0])

    def test_list_with_fallback_language(self):
        """Valida que los títulos hagan fallback a inglés con idioma no soportado."""
        headers = {'HTTP_ACCEPT_LANGUAGE': 'xx'}  # Idioma no soportado
        response = self.client.get(self.nodes_list_url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('title', response.data[0])

    # --- TESTS DE TIMEZONE ---

    def test_created_at_with_timezone_header(self):
        """Valida que created_at se convierta a la zona horaria especificada."""
        headers = {'HTTP_TIME_ZONE': 'America/New_York'}
        response = self.client.get(self.parent_url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('created_at', response.data)
        created_at = response.data['created_at']
        self.assertIsInstance(created_at, str)

    def test_created_at_with_invalid_timezone_fallback(self):
        """Valida que created_at haga fallback a UTC con zona horaria inválida."""
        headers = {'HTTP_TIME_ZONE': 'Invalid/Timezone'}
        response = self.client.get(self.parent_url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('created_at', response.data)
        created_at = response.data['created_at']
        # Debe contener UTC como fallback
        self.assertIn('UTC', created_at)

    # --- TESTS DE DEPTH PARAMETER ---

    def test_list_with_depth_zero(self):
        """Valida que ?depth=0 solo muestre nodos raíz sin hijos."""
        response = self.client.get(f"{self.nodes_list_url}?depth=0")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        parent_data = response.data[0]
        self.assertEqual(len(parent_data['children']), 0)

    def test_list_with_depth_one(self):
        """Valida que ?depth=1 muestre nodos raíz con hijos directos."""
        response = self.client.get(f"{self.nodes_list_url}?depth=1")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        parent_data = response.data[0]
        self.assertEqual(len(parent_data['children']), 1)
        self.assertEqual(len(parent_data['children'][0]['children']), 0)

    def test_list_with_depth_two(self):
        """Valida que ?depth=2 muestre hasta nietos."""
        # Crear un nieto para probar
        grandchild = Node.objects.create(content="Nieto_API", parent=self.child)
        
        response = self.client.get(f"{self.nodes_list_url}?depth=2")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        parent_data = response.data[0]
        hijo = parent_data['children'][0]
        self.assertEqual(len(hijo['children']), 1)

    def test_list_without_depth_parameter(self):
        """Valida que sin ?depth solo muestre hijos directos (default)."""
        response = self.client.get(self.nodes_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        parent_data = response.data[0]
        # Debe mostrar hijos directos
        self.assertEqual(len(parent_data['children']), 1)
        # Pero no nietos (sin profundidad)
        self.assertEqual(len(parent_data['children'][0]['children']), 0)

    def test_list_with_invalid_depth_parameter(self):
        """Valida que con depth inválido haga fallback a default."""
        response = self.client.get(f"{self.nodes_list_url}?depth=abc")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Debería comportarse como sin depth (solo hijos directos)
        parent_data = response.data[0]
        self.assertEqual(len(parent_data['children']), 1)
        self.assertEqual(len(parent_data['children'][0]['children']), 0)

    # --- TESTS DE PERMISSIONS ---

    def test_create_node_without_admin_permission(self):
        """Valida que usuarios no admin no puedan crear nodos."""
        # Crear usuario regular
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpassword',
            role='USER',
            is_email_confirmed=True
        )
        self.client.force_authenticate(user=regular_user)
        
        data = {'content': 'Nuevo Nodo', 'parent': None}
        response = self.client.post(self.nodes_list_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # nodes/tests.py
# nodes/tests.py
class NodeAPITest(APITestCase):
    """
    Suite de pruebas para validar los endpoints de la API, incluyendo:
    - Autenticación
    - Lógica de Borrado Lógico (Soft Delete)
    - Validación de ID (>= 1)
    - Internacionalización
    """
    def setUp(self):
        """Configuración de usuario con permisos y estructura de árbol."""
        # 1. CREAR Y AUTENTICAR AL USUARIO
        self.admin_user = User.objects.create_user(
            username='testadmin', 
            email='admin@test.com', 
            password='testpassword',
            role='ADMIN',
            is_email_confirmed=True
        )
        # 2. Loguear al cliente de prueba
        self.client.force_authenticate(user=self.admin_user)

        # 3. Crear un árbol: Padre -> Hijo
        self.parent = Node.objects.create(content="Padre_API")
        self.child = Node.objects.create(content="Hijo_API", parent=self.parent)
        
        self.parent_url = reverse('node-detail', kwargs={'pk': self.parent.pk})
        self.child_url = reverse('node-detail', kwargs={'pk': self.child.pk})
        self.nodes_list_url = reverse('node-list')
    
    # --- TESTS DE PERMISSIONS ---

    def test_create_node_without_admin_permission(self):
        """Valida que usuarios no admin no puedan crear nodos."""
        # Crear usuario regular
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpassword',
            role='USER',
            is_email_confirmed=True
        )
        self.client.force_authenticate(user=regular_user)
        
        data = {'content': 'Nuevo Nodo'}
        response = self.client.post(
            self.nodes_list_url, 
            data, 
            format='json'  # ← ESPECIFICAR FORMATO
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_node_with_admin_permission(self):
        """Valida que usuarios admin puedan crear nodos."""
        data = {'content': 'Nuevo Nodo Admin'}
        response = self.client.post(
            self.nodes_list_url, 
            data, 
            format='json'  # ← ESPECIFICAR FORMATO
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Nuevo Nodo Admin')
        self.assertIsNone(response.data['parent'])

    def test_create_child_node_with_admin_permission(self):
        """Valida que usuarios admin puedan crear nodos hijos."""
        data = {'content': 'Nuevo Hijo', 'parent': self.parent.id}
        response = self.client.post(
            self.nodes_list_url, 
            data, 
            format='json'  # ← ESPECIFICAR FORMATO
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Nuevo Hijo')
        self.assertEqual(response.data['parent'], self.parent.id)

    # --- También necesitas actualizar otros tests que usen POST ---

    def test_list_with_spanish_language(self):
        """Valida que los títulos se generen en español con header Accept-Language: es."""
        headers = {'HTTP_ACCEPT_LANGUAGE': 'es'}
        response = self.client.get(
            self.nodes_list_url, 
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('title', response.data[0])

    def test_list_with_english_language(self):
        """Valida que los títulos se generen en inglés con header Accept-Language: en."""
        headers = {'HTTP_ACCEPT_LANGUAGE': 'en'}
        response = self.client.get(
            self.nodes_list_url,
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('title', response.data[0])

    def test_created_at_with_timezone_header(self):
        """Valida que created_at se convierta a la zona horaria especificada."""
        headers = {'HTTP_TIME_ZONE': 'America/New_York'}
        response = self.client.get(
            self.parent_url,
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('created_at', response.data)
        created_at = response.data['created_at']
        self.assertIsInstance(created_at, str)

    # --- O crear un método helper para requests ---

    def _post_json(self, url, data):
        """Helper para hacer POST en formato JSON."""
        return self.client.post(url, data, format='json')
    
    def _get_with_headers(self, url, **headers):
        """Helper para hacer GET con headers."""
        return self.client.get(url, **headers)

    # Y luego usarlos así:
    def test_create_node_with_admin_permission_using_helper(self):
        """Valida que usuarios admin puedan crear nodos (usando helper)."""
        data = {'content': 'Nuevo Nodo Admin'}
        response = self._post_json(self.nodes_list_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Nuevo Nodo Admin')

# Test adicional para el modelo
class NodeModelTest(TestCase):
    """Pruebas específicas para el modelo Node."""
    
    def test_soft_delete_method(self):
        """Valida que soft_delete marque el nodo como borrado."""
        node = Node.objects.create(content="Test Soft Delete")
        
        self.assertFalse(node.is_deleted)
        self.assertIsNone(node.deleted_at)
        
        node.soft_delete()
        
        node.refresh_from_db()
        self.assertTrue(node.is_deleted)
        self.assertIsNotNone(node.deleted_at)

    def test_str_representation(self):
        """Valida la representación en string del modelo."""
        node = Node.objects.create(content="Test Node", id=99)
        self.assertEqual(str(node), "99: Test Node")

    def test_unique_constraint_enforcement(self):
        """Valida que la restricción de unicidad funcione correctamente."""
        parent = Node.objects.create(content="Padre")
        
        # Primer hijo - OK
        Node.objects.create(content="Hijo", parent=parent)
        
        # Segundo hijo con mismo contenido - Debe fallar
        with self.assertRaises(Exception):
            Node.objects.create(content="Hijo", parent=parent)