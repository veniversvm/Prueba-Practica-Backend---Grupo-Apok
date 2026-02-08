from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404 
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import pytz

from .mixins import ValidateIDMixin

from .models import Node
from .serializers import NodeSerializer, serializers

CACHE_TIMEOUT = 180
CACHE_VERSION_KEY = "node_list_cache_version"

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

@extend_schema_view(
    list=extend_schema(
        summary="Listar nodos raíz",
        description='''
Obtiene todos los nodos raíz del árbol jerárquico.

**Características:**
- Parámetro `depth` controla la profundidad (default: solo hijos directos)
- Header `Accept-Language` define el idioma para el campo `title`
- Header `Time-Zone` ajusta la zona horaria de `created_at`
- Cache automático de 180 segundos

**Ejemplos de uso:**
- `GET /api/nodes/` - Solo hijos directos (default)
- `GET /api/nodes/?depth=2` - Hasta nietos
- `GET /api/nodes/?depth=-1` - Profundidad infinita (limitada a 10 niveles)
''',
        parameters=[
            OpenApiParameter(
                name='depth',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='''
Niveles de profundidad a mostrar:
- `null` o no especificado: solo hijos directos (default)
- `0`: sin hijos
- `1`: hijos directos
- `2`: hijos + nietos
- `-1`: profundidad infinita (limitada a 10 niveles)
''',
                required=False,
                examples=[
                    OpenApiExample('Default (sin parámetro)', value=None),
                    OpenApiExample('Profundidad 2 niveles', value=2),
                    OpenApiExample('Profundidad infinita', value=-1),
                ]
            )
        ],
        responses={
            200: NodeSerializer(many=True),
            401: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='No autenticado'
            ),
        }
    ),
    retrieve=extend_schema(
        summary="Obtener nodo específico",
        description='Obtiene un nodo específico con sus descendientes según profundidad.',
        parameters=[
            OpenApiParameter(
                name='depth',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Niveles de profundidad a mostrar',
                required=False
            ),
            OpenApiParameter(
                name='Accept-Language',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                description='Idioma para el campo title (ej: es, en, fr)',
                required=False
            ),
            OpenApiParameter(
                name='Time-Zone',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                description='Zona horaria para created_at (ej: UTC, America/New_York)',
                required=False
            )
        ],
        responses={
            200: NodeSerializer,
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='''
Errores de validación:
- ID debe ser ≥ 1
- ID inválido (no numérico)
'''
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Nodo no encontrado'
            ),
        }
    ),
    create=extend_schema(
        summary="Crear nuevo nodo",
        description='''
Crea un nuevo nodo en el árbol.

**Permisos requeridos:** Rol ADMIN o SUDO
''',
        request=NodeSerializer,
        responses={
            201: NodeSerializer,
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='''
Errores de validación:
- Content duplicado en mismo nivel
- Auto-referencia
'''
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Permisos insuficientes'
            ),
        }
    ),
    update=extend_schema(
        summary="Actualizar nodo completo",
        description='Actualiza todos los campos de un nodo existente.',
        request=NodeSerializer,
        responses={
            200: NodeSerializer,
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Error de validación'
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Permisos insuficientes'
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Nodo no encontrado'
            ),
        }
    ),
    partial_update=extend_schema(
        summary="Actualizar nodo parcialmente",
        description='Actualiza campos específicos de un nodo existente.',
        request=NodeSerializer,
        responses={
            200: NodeSerializer,
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Error de validación'
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Permisos insuficientes'
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Nodo no encontrado'
            ),
        }
    ),
    destroy=extend_schema(
        summary="Eliminar nodo (soft delete)",
        description='''
Elimina lógicamente un nodo.

**Restricciones:**
- No se puede eliminar nodos con hijos activos
- Solo elimina nodos hoja
- Es un borrado lógico (is_deleted=True)

**Respuesta exitosa:** 200 OK con mensaje de confirmación
**Error:** 400 Bad Request si tiene hijos activos
''',
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Eliminación exitosa',
                examples=[
                    OpenApiExample(
                        'Ejemplo respuesta',
                        value={
                            "message": "Nodo 5 eliminado exitosamente.",
                            "id": 5
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='''
Errores:
- El nodo tiene hijos activos (code: has_children)
- ID inválido (< 1 o no numérico)
''',
                examples=[
                    OpenApiExample(
                        'Error: tiene hijos',
                        value={
                            "error": "No se puede eliminar un nodo que tiene hijos activos.",
                            "code": "has_children"
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Permisos insuficientes'
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Nodo no encontrado'
            ),
        }
    ),
    descendants=extend_schema(
        summary="Obtener descendientes de un nodo",
        description='Obtiene todos los descendientes de un nodo específico.',
        parameters=[
            OpenApiParameter(
                name='depth',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Niveles de profundidad a mostrar',
                required=False
            )
        ],
        responses={
            200: NodeSerializer,
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='ID inválido (< 1 o no numérico)'
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Nodo no encontrado'
            ),
        }
    )
)
class NodeViewSet(ValidateIDMixin, viewsets.ModelViewSet):
    """
    ViewSet para la gestión jerárquica de nodos.
    
    Características:
    - Bloquea operaciones con ID < 1 (via ValidateIDMixin)
    - Parámetro ?depth=N para controlar profundidad
    - Si no se pasa depth, solo muestra hijos directos
    - Cache diferenciado por profundidad
    """
    
    serializer_class = NodeSerializer
    
    def get_object(self):
        """
        Sobreescribir para obtener el objeto con validación adicional.
        """
        # Primero validar que el ID sea válido usando el mixin
        pk = self.kwargs.get('pk')
        
        # Validar usando el método del mixin
        is_valid, error_response = self.validate_id(pk)
        if not is_valid:
            # Si hay error, lanzar ValidationError para que DRF lo maneje
            raise serializers.ValidationError(error_response.data)
        
        # Obtener el queryset filtrado
        queryset = self.filter_queryset(self.get_queryset())
        
        # Realizar la búsqueda del objeto
        obj = get_object_or_404(queryset, pk=pk)
        
        # Verificar permisos
        self.check_object_permissions(self.request, obj)
        
        return obj
    
    def get_serializer_context(self):
        """
        Procesa headers y query parameters.
        """
        context = super().get_serializer_context()
        
        # --- Idioma ---
        accept_language = self.request.headers.get('Accept-Language', 'en')
        languages = accept_language.split(',')
        primary_lang = languages[0].strip()
        
        if '-' in primary_lang:
            language = primary_lang.split('-')[0]
        elif ';' in primary_lang:
            language = primary_lang.split(';')[0]
        else:
            language = primary_lang
        
        language = language[:2] if len(language) >= 2 else 'en'
        supported_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ar']
        context['language'] = language if language in supported_languages else 'en'
        
        # --- Zona Horaria ---
        tz_name = 'UTC'
        timezone_headers = ['Time-Zone', 'X-Timezone', 'Timezone', 'X-Time-Zone']
        
        for header_name in timezone_headers:
            header_value = self.request.headers.get(header_name)
            if header_value:
                tz_name = header_value.strip()
                break
        
        # Normalizar zona horaria
        tz_name = self.normalize_timezone(tz_name)
        if tz_name not in pytz.all_timezones:
            tz_name = 'UTC'
        
        context['user_timezone'] = tz_name
        
        # --- PARÁMETRO DE PROFUNDIDAD (CRÍTICO) ---
        depth_param = self.request.query_params.get('depth')
        
        if depth_param is not None:
            try:
                # Convertir a entero
                depth = int(depth_param)
                
                # Validar rangos
                if depth < -1:
                    depth = -1  # Profundidad infinita
                elif depth > 10:  # Límite por seguridad
                    depth = 10
                
                context['depth'] = depth
            except (ValueError, TypeError):
                # Si el valor no es válido, usar None (solo hijos directos)
                context['depth'] = None
        else:
            # Si no se pasa el parámetro, usar None (solo hijos directos)
            context['depth'] = None
        
        # Depth actual para recursión (siempre empieza en 0)
        context['current_depth'] = 0
        
        return context
    
    def normalize_timezone(self, tz_name):
        """Normaliza nombres de zonas horarias."""
        if not tz_name:
            return 'UTC'
        
        tz_name = tz_name.strip().upper()
        
        timezone_map = {
            'UTC': 'UTC',
            'GMT': 'UTC',
            'EST': 'America/New_York',
            'EDT': 'America/New_York',
            'CST': 'America/Chicago',
            'CDT': 'America/Chicago',
            'MST': 'America/Denver',
            'MDT': 'America/Denver',
            'PST': 'America/Los_Angeles',
            'PDT': 'America/Los_Angeles',
            'CET': 'Europe/Paris',
            'CEST': 'Europe/Paris',
        }
        
        if tz_name in timezone_map:
            return timezone_map[tz_name]
        
        if '/' in tz_name:
            parts = tz_name.split('/')
            normalized = '/'.join([parts[0].capitalize()] + [p.capitalize() for p in parts[1:]])
            return normalized
        
        return tz_name
    
    def _get_cache_version(self):
        return cache.get(CACHE_VERSION_KEY, 1)
    
    def _invalidate_list_cache(self):
        version = self._get_cache_version()
        cache.set(CACHE_VERSION_KEY, version + 1)
    
    def _get_cache_key_func(self, request):
        """
        Función nombrada para generar claves de cache.
        """
        # Crear contexto temporal para extraer parámetros
        temp_context = self.get_serializer_context()
        
        version = self._get_cache_version()
        language = temp_context.get('language', 'en')
        timezone = temp_context.get('user_timezone', 'UTC')
        depth = temp_context.get('depth', 'none')  # 'none' si no se especifica
        
        # Generar una clave segura para cache
        # Eliminar caracteres problemáticos
        safe_language = language.replace('-', '_').replace(' ', '_')
        safe_timezone = timezone.replace('/', '_').replace(' ', '_')
        
        return f"node_list_v{version}_lang_{safe_language}_tz_{safe_timezone}_depth_{depth}"
    
    @method_decorator(
        cache_page(
            CACHE_TIMEOUT,
            key_prefix="node_list"
        )
    )
    def list(self, request, *args, **kwargs):
        """
        Lista nodos raíz con control de profundidad.
        """
        # Usar una versión más simple del cache key
        return super().list(request, *args, **kwargs)
    
    def get_cache_key(self, request):
        """
        Genera clave de cache incluyendo profundidad.
        """
        # Crear contexto temporal para extraer parámetros
        temp_context = self.get_serializer_context()
        
        version = self._get_cache_version()
        language = temp_context.get('language', 'en')
        timezone = temp_context.get('user_timezone', 'UTC')
        depth = temp_context.get('depth', 'none')  # 'none' si no se especifica
        
        return f"node_list_v{version}_lang_{language}_tz_{timezone}_depth_{depth}"
    
    def get_queryset(self):
        """
        Filtra nodos según la acción.
        Excluye IDs < 1 por seguridad.
        """
        queryset = Node.objects.filter(is_deleted=False)
        
        # Filtrar IDs < 1 por seguridad (aunque no deberían existir)
        queryset = queryset.filter(id__gte=1)
        
        if self.action == "list":
            # Solo nodos raíz para el listado principal
            return queryset.filter(parent__isnull=True)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def descendants(self, request, pk=None):
        """
        Endpoint adicional: Obtener descendientes de un nodo específico.
        
        Ejemplo: GET /api/nodes/1/descendants/?depth=2
        
        Nota: La validación de ID se hace en el mixin.
        """
        # El mixin ya validó el ID en initial()
        node = self.get_object()
        serializer_context = self.get_serializer_context()
        
        # Asegurar que empezamos desde el nodo actual
        serializer_context['current_depth'] = 0
        
        serializer = self.get_serializer(node, context=serializer_context)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        self._invalidate_list_cache()
        serializer.save()
    
    def perform_update(self, serializer):
        self._invalidate_list_cache()
        serializer.save()
    
    def retrieve(self, request, *args, **kwargs):
        """
        Obtiene un nodo específico CON profundidad.
        
        Ejemplo: GET /nodes/5/?depth=3
        
        Nota: La validación de ID se hace en el mixin.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Elimina lógicamente un nodo si no tiene hijos activos.
        
        Nota: La validación de ID se hace en el mixin.
        """
        instance = self.get_object()
        
        if instance.children.filter(is_deleted=False).exists():
            return Response(
                {
                    "error": "No se puede eliminar un nodo que tiene hijos activos.",
                    "code": "has_children"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        self._invalidate_list_cache()
        instance.soft_delete()
        
        return Response(
            {
                "message": f"Nodo {instance.id} eliminado exitosamente.",
                "id": instance.id
            },
            status=status.HTTP_200_OK
        )
    
    def get_permissions(self):
        """
        Configura permisos según la acción.
        """
        from nodes.permissions import IsActiveAndConfirmed, IsAdminUserCustom
        
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUserCustom()]
        return [IsActiveAndConfirmed()]

@extend_schema(
    summary="Obtener árbol completo",
    description='''
Obtiene árboles completos desde nodos raíz específicos o todos los árboles.

**Parámetros opcionales:**
- `root_id`: ID del nodo raíz específico
- `depth`: Profundidad máxima a mostrar
''',
    parameters=[
        OpenApiParameter(
            name='root_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='ID del nodo raíz específico',
            required=False
        ),
        OpenApiParameter(
            name='depth',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Niveles de profundidad a mostrar',
            required=False
        )
    ],
    responses={
        200: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description='Árbol o lista de árboles'
        ),
        404: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description='Nodo raíz no encontrado'
        ),
    }
)
class NodeTreeView(APIView):
    """
    Vista especializada para obtener árboles completos.
    """
    
    def get(self, request):
        """
        Obtiene árboles completos con control de profundidad.
        
        Parámetros:
        - root_id: ID del nodo raíz (opcional, si no se especifica, todos los raíces)
        - depth: Profundidad máxima (opcional, default: mostrar solo hijos directos)
        """
        from .serializers import NodeSerializer
        
        # Obtener parámetros
        root_id = request.query_params.get('root_id')
        depth_param = request.query_params.get('depth')
        
        # Procesar depth
        depth = None
        if depth_param is not None:
            try:
                depth = int(depth_param)
                if depth < -1:
                    depth = -1
                elif depth > 10:
                    depth = 10
            except (ValueError, TypeError):
                depth = None
        
        # Contexto para el serializador
        context = {
            'request': request,
            'language': 'en',  # Deberías extraer del header
            'user_timezone': 'UTC',  # Deberías extraer del header
            'depth': depth,
            'current_depth': 0
        }
        
        # Filtrar nodos
        queryset = Node.objects.filter(is_deleted=False)
        
        if root_id:
            # Árbol específico desde un nodo raíz
            try:
                root_node = queryset.get(id=root_id, parent__isnull=True)
                serializer = NodeSerializer(root_node, context=context)
                return Response([serializer.data])
            except Node.DoesNotExist:
                return Response(
                    {"error": f"Nodo raíz con ID {root_id} no encontrado."},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Todos los árboles (todos los nodos raíz)
            root_nodes = queryset.filter(parent__isnull=True)
            serializer = NodeSerializer(root_nodes, many=True, context=context)
            return Response(serializer.data)