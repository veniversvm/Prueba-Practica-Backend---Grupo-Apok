from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404 
from django.http import Http404
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import pytz

from .mixins import ValidateIDMixin
from .models import Node
from .serializers import NodeSerializer

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
        pk = self.kwargs.get('pk')
        
        # Validar usando el método del mixin
        is_valid, error_data = self.validate_id(pk)
        if not is_valid:
            raise ValidationError(error_data)
        
        try:
            # Usar get_object_or_404 con el queryset filtrado
            queryset = self.filter_queryset(self.get_queryset())
            obj = queryset.get(pk=pk)
        except Node.DoesNotExist:
            raise Http404(f"Nodo con ID {pk} no encontrado o está eliminado")
        
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
    
    # def _get_cache_version(self):
    #     return cache.get(CACHE_VERSION_KEY, 1)
    
    # def _invalidate_list_cache(self):
    #     version = self._get_cache_version()
    #     cache.set(CACHE_VERSION_KEY, version + 1)
    
    # def _get_cache_key(self):
    #     """
    #     Genera clave de cache considerando todos los parámetros.
    #     """
    #     # Usar get_serializer_context para obtener parámetros consistentes
    #     context = self.get_serializer_context()
        
    #     version = self._get_cache_version()
    #     language = context.get('language', 'en')
    #     timezone = context.get('user_timezone', 'UTC')
    #     depth = context.get('depth', 'none')
        
    #     # Crear clave segura
    #     safe_key = f"node_list:v{version}:lang:{language}:tz:{timezone}:depth:{depth}"
        
    #     # Si hay query params adicionales, incluirlos
    #     query_params = []
    #     for key, value in sorted(self.request.GET.items()):
    #         if key != 'depth':  # Ya lo incluimos
    #             query_params.append(f"{key}:{value}")
        
    #     if query_params:
    #         safe_key += f":{'|'.join(query_params)}"
        
    #     # Incluir información de usuario si está autenticado
    #     if self.request.user.is_authenticated:
    #         safe_key += f":user:{self.request.user.id}"
        
    #     return safe_key
    
    @method_decorator(cache_page(CACHE_TIMEOUT))
    def list(self, request, *args, **kwargs):
        """
        Lista nodos raíz con control de profundidad.
        Usa cache_page nativo de Django.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    # ELIMINA estos métodos si existen:
    # _get_cache_version
    # _invalidate_list_cache  
    # _get_cache_key
    
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
        """
        # El mixin ya validó el ID en initial()
        node = self.get_object()
        serializer_context = self.get_serializer_context()
        
        # Asegurar que empezamos desde el nodo actual
        serializer_context['current_depth'] = 0
        
        serializer = self.get_serializer(node, context=serializer_context)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        cache.clear()  # O cache.delete_pattern('*nodes*') si usas redis
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        cache.clear()
        serializer.save(created_by=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Obtiene un nodo específico CON profundidad.
        
        Ejemplo: GET /nodes/5/?depth=3
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if instance.children.filter(is_deleted=False).exists():
            return Response(
                {
                    "error": "No se puede eliminar un nodo que tiene hijos activos.",
                    "code": "has_children"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        cache.clear()
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
    Vista para obtener árboles completos de nodos.
    """
    
    def get_permissions(self):
        """
        Usar los mismos permisos que NodeViewSet para list.
        """
        from nodes.permissions import IsActiveAndConfirmed
        return [IsActiveAndConfirmed()]
    
    def get(self, request):
        """
        Obtiene árbol(es) completo(s).
        """
        from nodes.serializers import NodeSerializer
        
        root_id = request.query_params.get('root_id')
        depth_param = request.query_params.get('depth')
        
        # Procesar profundidad
        depth = None
        if depth_param is not None:
            try:
                depth = int(depth_param)
                if depth < -1:
                    depth = -1
                elif depth > 10:
                    depth = 10
            except (ValueError, TypeError):
                pass
        
        # Contexto para el serializador
        context = {
            'language': request.headers.get('Accept-Language', 'en')[:2],
            'user_timezone': request.headers.get('Time-Zone', 'UTC'),
            'depth': depth,
            'current_depth': 0,
            'request': request
        }
        
        # Normalizar idioma
        language = context['language']
        supported_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ar']
        context['language'] = language if language in supported_languages else 'en'
        
        # Normalizar zona horaria
        tz_name = context['user_timezone']
        if tz_name not in pytz.all_timezones:
            context['user_timezone'] = 'UTC'
        
        if root_id:
            # Árbol específico
            try:
                root_node = Node.objects.get(
                    id=root_id,
                    is_deleted=False,
                    parent__isnull=True
                )
                serializer = NodeSerializer(root_node, context=context)
                return Response(serializer.data)
            except Node.DoesNotExist:
                return Response(
                    {"error": f"Nodo raíz con ID {root_id} no encontrado"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Todos los árboles
            root_nodes = Node.objects.filter(
                is_deleted=False,
                parent__isnull=True
            )
            serializer = NodeSerializer(root_nodes, many=True, context=context)
            return Response(serializer.data)