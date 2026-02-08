# app_nodos/nodes/serializers.py
from rest_framework import serializers
from .models import Node
from num2words import num2words
import pytz
from django.utils import timezone as django_timezone
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer, OpenApiExample
from drf_spectacular.types import OpenApiTypes

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Ejemplo de nodo raíz',
            value={
                "id": 1,
                "content": "Nodo raíz",
                "title": "one",
                "parent": None,
                "created_at": "2024-01-15 10:00:00",
                "children": [
                    {
                        "id": 2,
                        "content": "Hijo",
                        "title": "two",
                        "parent": 1,
                        "created_at": "2024-01-15 10:05:00",
                        "children": []
                    }
                ]
            },
            description='Ejemplo de nodo raíz con un hijo (depth=None o depth=1)'
        ),
        OpenApiExample(
            'Ejemplo de nodo con profundidad 2',
            value={
                "id": 1,
                "content": "Nodo raíz",
                "title": "uno",
                "parent": None,
                "created_at": "2024-01-15 10:00:00",
                "children": [
                    {
                        "id": 2,
                        "content": "Hijo",
                        "title": "dos",
                        "parent": 1,
                        "created_at": "2024-01-15 10:05:00",
                        "children": [
                            {
                                "id": 3,
                                "content": "Nieto",
                                "title": "tres",
                                "parent": 2,
                                "created_at": "2024-01-15 10:07:00",
                                "children": []
                            }
                        ]
                    }
                ]
            },
            description='Ejemplo con depth=2 (hasta nietos)'
        ),
        OpenApiExample(
            'Ejemplo de nodo hoja',
            value={
                "id": 4,
                "content": "Nodo hoja",
                "title": "four",
                "parent": 2,
                "created_at": "2024-01-15 10:08:00",
                "children": []
            },
            description='Ejemplo de nodo sin hijos'
        ),
    ],
    component_name='Node',
    description='''
Serializador para el modelo Node con características avanzadas:

**Campos calculados dinámicamente:**
1. **title**: Representación textual del ID según idioma del header Accept-Language
   - Ejemplo: ID=1 → "one" (en), "uno" (es), "un" (fr)
   - Idiomas soportados: en, es, fr, de, it, pt, ru, ar
   - Fallback a inglés si idioma no soportado

2. **children**: Lista de hijos con control de profundidad recursiva
   - Controlado por parámetro de query ?depth=N
   - Lógica de profundidad:
     - depth=None: solo hijos directos (default)
     - depth=0: sin hijos
     - depth=1: hijos directos (sin nietos)
     - depth=2: hijos + nietos
     - depth=-1: todos los niveles (limitado a 10 por seguridad)

3. **created_at**: Fecha de creación en zona horaria personalizada
   - Se ajusta según header Time-Zone
   - Formato: "YYYY-MM-DD HH:MM:SS"
   - Fallback a UTC si zona horaria inválida

**Validaciones implementadas:**
- Unicidad: No puede haber dos nodos con mismo content bajo mismo parent
- Auto-referencia: Un nodo no puede ser su propio padre
- ID validation: IDs deben ser ≥ 1 (solo lectura, generado automáticamente)
'''
)
class NodeSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Node.
    
    Características:
    - Control de profundidad recursiva
    - Si no se pasa profundidad, solo muestra hijos directos
    """
    
    
    title = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    created_by = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    
    class Meta:
        model = Node
        fields = ['id', 'content', 'title', 'parent', 'children', 'created_at', 'created_by', 'is_deleted']
        read_only_fields = ['id', 'title', 'created_at', 'created_by']
    
    def get_title(self, obj):
        """Genera título en el idioma solicitado."""
        language = self.context.get('language', 'en')
        valid_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ar']
        
        if language not in valid_languages:
            language = 'en'
        
        try:
            return num2words(obj.id, lang=language)
        except Exception:
            return num2words(obj.id, lang='en')
    
    def get_children(self, obj):
        """
        Implementa la lógica de profundidad recursiva.
        
        Reglas:
        - depth=None: solo hijos directos (default)
        - depth=0: sin hijos
        - depth=1: hijos directos (sin nietos)
        - depth=2: hijos + nietos
        - depth=-1: todos los niveles (limitado a 10 por seguridad)
        """
        # Obtener parámetros de profundidad del contexto
        depth = self.context.get('depth', None)
        current_depth = self.context.get('current_depth', 0)
        
        # Si depth es None, comportamiento por defecto: solo hijos directos
        if depth is None:
            # Lógica para hijos directos
            active_children = obj.children.filter(is_deleted=False)
            return NodeSerializer(
                active_children,
                many=True,
                context={
                    'language': self.context.get('language', 'en'),
                    'user_timezone': self.context.get('user_timezone', 'UTC'),
                    'depth': 0,  # IMPORTANTE: hijos no muestran nietos
                    'current_depth': current_depth + 1
                }
            ).data
        
        # Si depth = 0, no mostrar hijos
        if depth == 0:
            return []
        
        # Calcular si podemos mostrar más niveles
        can_show_more = False
        
        if depth == -1:  # Profundidad infinita
            # Limitar a 10 niveles por seguridad
            can_show_more = current_depth < 10
        elif depth > 0:
            can_show_more = current_depth < depth
        
        if not can_show_more:
            return []
        
        # Obtener hijos activos
        active_children = obj.children.filter(is_deleted=False)
        
        return NodeSerializer(
            active_children,
            many=True,
            context={
                'language': self.context.get('language', 'en'),
                'user_timezone': self.context.get('user_timezone', 'UTC'),
                'depth': depth,
                'current_depth': current_depth + 1
            }
        ).data

    def get_created_at(self, obj):
        """Convierte created_at a la zona horaria solicitada."""
        tz_name = self.context.get('user_timezone', 'UTC')
        
        utc_datetime = obj.created_at
        if django_timezone.is_naive(utc_datetime):
            utc_datetime = django_timezone.make_aware(utc_datetime, django_timezone.utc)
        
        try:
            if tz_name not in pytz.all_timezones:
                raise pytz.exceptions.UnknownTimeZoneError()
            
            user_tz = pytz.timezone(tz_name)
            local_datetime = utc_datetime.astimezone(user_tz)
            return local_datetime.strftime('%Y-%m-%d %H:%M:%S')
            
        except Exception:
            fallback_datetime = utc_datetime.astimezone(pytz.UTC)
            return fallback_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    def validate(self, data):
        """Validaciones de negocio."""
        content = data.get('content', getattr(self.instance, 'content', None))
        parent = data.get('parent', getattr(self.instance, 'parent', None))

        queryset = Node.objects.filter(
            content__iexact=content, 
            parent=parent, 
            is_deleted=False
        )
        
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError({
                "content": f"Ya existe un nodo activo con el contenido '{content}' en este nivel."
            })

        if self.instance and parent and parent.pk == self.instance.pk:
            raise serializers.ValidationError({
                "parent": "Un nodo no puede ser su propio padre."
            })

        return data
    
    def to_internal_value(self, data):
        """
        Validación antes de procesar los datos.
        Útil para operaciones de creación/actualización.
        """
        # Si hay un 'id' en los datos, validarlo
        if 'id' in data and data['id'] is not None:
            try:
                id_value = int(data['id'])
                if id_value < 1:
                    raise serializers.ValidationError({
                        'id': 'El ID debe ser un número positivo mayor o igual a 1.'
                    })
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'id': 'ID inválido. Debe ser un número entero.'
                })
        
        return super().to_internal_value(data)