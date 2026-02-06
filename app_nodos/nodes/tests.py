from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from nodes.models import Node
from nodes.serializers import NodeSerializer

User = get_user_model()


class NodeSerializerTest(TestCase):
    """
    Suite de pruebas para validar la lógica de negocio y la serialización
    implementadas en el NodeSerializer.

    Cubre: Conversión de números, unicidad, jerarquía y profundidad.
    """
    def setUp(self):
        """Configuración de la estructura base del árbol para pruebas."""
        # Se asume que el usuario admin_user ya fue creado en la suite APITestCase
        self.root_node = Node.objects.create(title="Abuelo")
        self.child_node = Node.objects.create(title="Padre", parent=self.root_node)
        self.grandchild_node = Node.objects.create(title="Hijo", parent=self.child_node)

    # --- TESTS DE POST (Deserialización / Saneamiento) ---

    def test_title_conversion_to_spanish(self):
        """Valida que la conversión de '1' a 'uno' funcione con Accept-Language: es."""
        data = {'title': '1'}
        context = {'language': 'es'}
        serializer = NodeSerializer(data=data, context=context)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['title'], 'uno')

    def test_title_conversion_to_english(self):
        """Valida que la conversión de '5' a 'five' funcione con Accept-Language: en."""
        data = {'title': '5'}
        context = {'language': 'en'}
        serializer = NodeSerializer(data=data, context=context)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['title'], 'five')

    def test_sanitization_whitespace(self):
        """Valida la limpieza de espacios en blanco al inicio/final del título."""
        data = {'title': '   Nodo Limpio   '}
        serializer = NodeSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['title'], 'Nodo Limpio')

    def test_validation_self_parenting(self):
        """Valida que un nodo no pueda referenciarse a sí mismo como padre (ciclo infinito)."""
        data = {'title': 'Error', 'parent': self.root_node.id}
        serializer = NodeSerializer(instance=self.root_node, data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('parent', serializer.errors)

    def test_unique_title_at_same_level(self):
        """Valida que no se puedan crear dos nodos con el mismo nombre bajo el mismo padre."""
        # 'Padre' ya existe bajo 'Abuelo'.
        data = {'title': 'Padre', 'parent': self.root_node.id}
        serializer = NodeSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    # --- TESTS DE GET (Serialización / Depth) ---

    def test_serialization_depth_zero(self):
        """Valida que con depth=0 solo se retorne la raíz (sin hijos)."""
        context = {'max_depth': 0, 'current_depth': 0}
        serializer = NodeSerializer(self.root_node, context=context)
        
        self.assertEqual(len(serializer.data['children']), 0)

    def test_serialization_depth_one(self):
        """Valida que con depth=1 se retorne el primer nivel de hijos, pero no el segundo."""
        context = {'max_depth': 1, 'current_depth': 0}
        serializer = NodeSerializer(self.root_node, context=context)
        
        # Debe tener 1 hijo directo (Padre)
        self.assertEqual(len(serializer.data['children']), 1)
        # El hijo directo no debe tener sus propios hijos cargados (Hijo)
        self.assertEqual(len(serializer.data['children'][0]['children']), 0)

    def test_serialization_depth_two(self):
        """Valida que con depth=2 se retorne la jerarquía completa (Abuelo -> Padre -> Hijo)."""
        context = {'max_depth': 2, 'current_depth': 0}
        serializer = NodeSerializer(self.root_node, context=context)
        
        # Verificamos que el nieto exista
        padre = serializer.data['children'][0]
        self.assertTrue(len(padre['children']) > 0)
        self.assertEqual(padre['children'][0]['title'], 'Hijo')


class NodeAPITest(APITestCase):
    """
    Suite de pruebas para validar los endpoints de la API, incluyendo:
    - Autenticación (simulación JWT).
    - Lógica de Borrado Lógico (Soft Delete).
    - Integridad referencial.
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
        # 2. Loguear al cliente de prueba simulando el token JWT
        self.client.force_authenticate(user=self.admin_user)

        # 3. Crear un árbol: Padre -> Hijo
        self.parent = Node.objects.create(
            title="Padre_API", 
            created_by=self.admin_user, 
            updated_by=self.admin_user
        )
        self.child = Node.objects.create(
            title="Hijo_API", 
            parent=self.parent,
            created_by=self.admin_user, 
            updated_by=self.admin_user
        )
        
        self.parent_url = reverse('node-detail', kwargs={'pk': self.parent.pk})
        self.child_url = reverse('node-detail', kwargs={'pk': self.child.pk})

    def test_delete_leaf_node_success(self):
        """Valida que borrar un nodo hoja resulte en 204 y lo oculte."""
        response = self.client.delete(self.child_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verifica que solo queda 1 nodo no borrado lógicamente (el padre)
        self.assertEqual(Node.objects.filter(is_deleted=False).count(), 1)
        self.assertTrue(Node.objects.filter(is_deleted=True, pk=self.child.pk).exists())

    def test_delete_parent_node_fails(self):
        """Valida que borrar un nodo con hijos activos resulte en 400."""
        response = self.client.delete(self.parent_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No se puede eliminar un nodo que tiene hijos activos.", response.data['error'])
        # Verifica que el nodo padre NO se haya borrado
        self.assertFalse(Node.objects.get(pk=self.parent.pk).is_deleted)
        