from django.test import TestCase
from nodes.models import Node
from nodes.serializers import NodeSerializer

class NodeSerializerTest(TestCase):
    def setUp(self):
        # Creamos una estructura base: Abuelo -> Padre -> Hijo
        self.root_node = Node.objects.create(title="Abuelo")
        self.child_node = Node.objects.create(title="Padre", parent=self.root_node)
        self.grandchild_node = Node.objects.create(title="Hijo", parent=self.child_node)

    # --- TESTS DE POST (Deserialización / Saneamiento) ---

    def test_title_conversion_to_spanish(self):
        """Validar que '1' se convierta en 'uno' con header 'es'"""
        data = {'title': '1'}
        context = {'language': 'es'}
        serializer = NodeSerializer(data=data, context=context)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['title'], 'uno')

    def test_title_conversion_to_english(self):
        """Validar que '5' se convierta en 'five' con header 'en'"""
        data = {'title': '5'}
        context = {'language': 'en'}
        serializer = NodeSerializer(data=data, context=context)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['title'], 'five')

    def test_sanitization_whitespace(self):
        """Validar que se limpien los espacios en blanco"""
        data = {'title': '   Nodo Limpio   '}
        serializer = NodeSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['title'], 'Nodo Limpio')

    def test_validation_self_parenting(self):
        """Validar que un nodo no pueda ser su propio padre"""
        data = {'title': 'Error', 'parent': self.root_node.id}
        # Pasamos la instancia existente para que el validador detecte el conflicto
        serializer = NodeSerializer(instance=self.root_node, data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('parent', serializer.errors)

    # --- TESTS DE GET (Serialización / Depth) ---

    def test_serialization_depth_zero(self):
        """Con depth 0, children debe estar vacío aunque existan en DB"""
        context = {'max_depth': 0, 'current_depth': 0}
        serializer = NodeSerializer(self.root_node, context=context)
        
        self.assertEqual(len(serializer.data['children']), 0)

    def test_serialization_depth_one(self):
        """Con depth 1, debe traer al hijo pero no al nieto"""
        context = {'max_depth': 1, 'current_depth': 0}
        serializer = NodeSerializer(self.root_node, context=context)
        
        # Tiene 1 hijo (Padre)
        self.assertEqual(len(serializer.data['children']), 1)
        # El hijo no debe tener sus propios hijos cargados (Hijo)
        self.assertEqual(len(serializer.data['children'][0]['children']), 0)

    def test_serialization_depth_two(self):
        """Con depth 2, debe traer toda la jerarquía"""
        context = {'max_depth': 2, 'current_depth': 0}
        serializer = NodeSerializer(self.root_node, context=context)
        
        # Root -> Padre -> Hijo
        padre = serializer.data['children'][0]
        hijo = padre['children'][0]
        self.assertEqual(hijo['title'], 'Hijo')