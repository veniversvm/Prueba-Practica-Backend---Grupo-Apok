# app_nodos/users/views.py
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

# Importaciones condicionales para evitar errores circulares
try:
    from nodes.serializers import NodeSerializer 
    from nodes.models import Node 
    HAS_NODES_APP = True
except ImportError:
    NodeSerializer = None
    Node = None
    HAS_NODES_APP = False

from .models import User
from .serializers import UserSerializer, UserDetailSerializer, UserCreateSerializer
from .permissions import IsAdminUserCustom, IsActiveAndConfirmed, IsOwnerOrAdmin


# ============================================================================
# DOCUMENTACIÓN OPENAPI/SPECTACULAR
# ============================================================================
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="Listar usuarios",
        description='''
        Obtiene la lista de usuarios según los permisos del usuario autenticado.
        
        **Reglas de visibilidad por rol:**
        - **SUDO**: Ve todos los usuarios (excepto eliminados)
        - **ADMIN**: Ve todos los usuarios excepto SUDO
        - **USER**: Solo ve su propio perfil
        
        **Características:**
        - Filtros dinámicos por rol, estado de confirmación y actividad
        - Búsqueda en username, email, nombre y apellido
        - Ordenamiento múltiple por diferentes campos
        - Excluye automáticamente usuarios eliminados (soft delete)
        
        **Ejemplos de uso:**
        - `GET /api/users/` - Lista según permisos
        - `GET /api/users/?role=ADMIN` - Solo administradores
        - `GET /api/users/?search=johndoe` - Buscar usuario
        - `GET /api/users/?ordering=-date_joined` - Ordenar por fecha descendente
        ''',
        parameters=[
            OpenApiParameter(
                name='role',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filtrar por rol del usuario',
                enum=['SUDO', 'ADMIN', 'USER']
            ),
            OpenApiParameter(
                name='is_email_confirmed',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filtrar por estado de confirmación de email (true/false)'
            ),
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filtrar por estado activo/inactivo (true/false)'
            ),
            OpenApiParameter(
                name='is_deleted',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filtrar por estado de eliminación lógica (true/false)'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Buscar texto en: username, email, first_name, last_name, role'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='''
                Campo(s) para ordenar resultados. Múltiples campos separados por coma.
                Campos disponibles: username, email, date_joined, role, is_active
                Prefijo '-' para orden descendente.
                Ejemplo: `ordering=-date_joined,username`
                '''
            ),
        ],
        responses={
            200: UserSerializer(many=True),
            401: OpenApiResponse(description='No autenticado'),
            403: OpenApiResponse(description='Permisos insuficientes')
        },
        examples=[
            OpenApiExample(
                'Listado para SUDO',
                value=[
                    {
                        'id': 1,
                        'username': 'superadmin',
                        'email': 'admin@system.com',
                        'role': 'SUDO',
                        'is_email_confirmed': True,
                        'is_active': True,
                        'is_deleted': False,
                        'date_joined': '2024-01-01T12:00:00Z'
                    },
                    {
                        'id': 2,
                        'username': 'siteadmin',
                        'email': 'admin@site.com',
                        'role': 'ADMIN',
                        'is_email_confirmed': True,
                        'is_active': True,
                        'is_deleted': False,
                        'date_joined': '2024-01-02T10:00:00Z'
                    }
                ],
                description='SUDO ve todos los usuarios incluyendo otros SUDO'
            ),
            OpenApiExample(
                'Listado para ADMIN',
                value=[
                    {
                        'id': 2,
                        'username': 'siteadmin',
                        'email': 'admin@site.com',
                        'role': 'ADMIN',
                        'is_email_confirmed': True,
                        'is_active': True,
                        'is_deleted': False,
                        'date_joined': '2024-01-02T10:00:00Z'
                    },
                    {
                        'id': 3,
                        'username': 'johndoe',
                        'email': 'john.doe@example.com',
                        'role': 'USER',
                        'is_email_confirmed': True,
                        'is_active': True,
                        'is_deleted': False,
                        'date_joined': '2024-01-03T08:00:00Z'
                    }
                ],
                description='ADMIN ve todos los usuarios excepto SUDO'
            ),
            OpenApiExample(
                'Listado para USER',
                value=[
                    {
                        'id': 3,
                        'username': 'johndoe',
                        'email': 'john.doe@example.com',
                        'role': 'USER',
                        'is_email_confirmed': True,
                        'is_active': True,
                        'is_deleted': False,
                        'date_joined': '2024-01-03T08:00:00Z'
                    }
                ],
                description='USER solo ve su propio perfil'
            )
        ]
    ),
    retrieve=extend_schema(
        summary="Obtener detalle de usuario",
        description='''
        Obtiene el detalle completo de un usuario específico.
        
        **Incluye métricas extendidas:**
        - `nodes_created_count`: Número de nodos activos creados por el usuario
        - `role_display`: Nombre completo del rol (para mostrar en UI)
        
        **Validaciones de acceso:**
        - SUDO: Puede ver cualquier usuario
        - ADMIN: Puede ver cualquier usuario excepto SUDO
        - USER: Solo puede verse a sí mismo
        
        **Usuarios eliminados:** No son accesibles a través de este endpoint
        ''',
        responses={
            200: UserDetailSerializer,
            401: OpenApiResponse(description='No autenticado'),
            403: OpenApiResponse(description='Permisos insuficientes'),
            404: OpenApiResponse(description='Usuario no encontrado o eliminado')
        },
        examples=[
            OpenApiExample(
                'Detalle de usuario ADMIN',
                value={
                    'id': 2,
                    'username': 'siteadmin',
                    'email': 'admin@site.com',
                    'first_name': 'Site',
                    'last_name': 'Manager',
                    'role': 'ADMIN',
                    'role_display': 'Administrador',
                    'is_email_confirmed': True,
                    'is_active': True,
                    'is_deleted': False,
                    'date_joined': '2024-01-02T10:00:00Z',
                    'last_login': '2024-01-14T14:20:00Z',
                    'nodes_created_count': 5
                }
            )
        ]
    ),
    create=extend_schema(
        summary="Crear nuevo usuario",
        description='''
        Crea un nuevo usuario en el sistema con rol específico.
        
        **Permisos requeridos:**
        - SUDO: Puede crear usuarios con cualquier rol (SUDO, ADMIN, USER)
        - ADMIN: Puede crear usuarios con roles ADMIN o USER
        - USER: No puede crear usuarios
        
        **Validaciones estrictas:**
        1. Solo SUDO puede crear otros usuarios SUDO
        2. Email debe ser único en todo el sistema
        3. Username debe ser único
        4. Contraseña mínimo 8 caracteres
        5. Las contraseñas deben coincidir (password_confirm)
        
        **Campos obligatorios:**
        - username, email, password, password_confirm
        
        **Campos opcionales:**
        - role (default: USER), first_name, last_name
        
        **Flujo post-creación:**
        - is_email_confirmed = False por defecto (seguridad)
        - Usuario debe confirmar email para autenticarse
        ''',
        request=UserCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=UserSerializer,
                description='Usuario creado exitosamente'
            ),
            400: OpenApiResponse(description='Error de validación en los datos'),
            403: OpenApiResponse(description='Permisos insuficientes para crear este rol')
        },
        examples=[
            OpenApiExample(
                'Crear usuario USER',
                value={
                    'username': 'newuser',
                    'email': 'new.user@example.com',
                    'password': 'SecurePass123!',
                    'password_confirm': 'SecurePass123!',
                    'role': 'USER',
                    'first_name': 'New',
                    'last_name': 'User'
                },
                description='Creación básica de usuario regular'
            ),
            OpenApiExample(
                'Crear usuario ADMIN (solo SUDO)',
                value={
                    'username': 'newadmin',
                    'email': 'new.admin@example.com',
                    'password': 'AdminPass456!',
                    'password_confirm': 'AdminPass456!',
                    'role': 'ADMIN',
                    'first_name': 'New',
                    'last_name': 'Admin'
                },
                description='Creación de administrador (requiere SUDO)'
            )
        ]
    ),
    update=extend_schema(
        summary="Actualizar usuario completo (PUT)",
        description='''
        Actualiza todos los campos de un usuario existente.
        
        **Reglas de edición estrictas:**
        1. USER: Solo puede editar su propio perfil (no puede cambiar rol)
        2. ADMIN: Puede editar usuarios USER, pero no SUDO u otros ADMIN
        3. SUDO: Puede editar cualquier usuario
        
        **Restricciones especiales:**
        - No se puede modificar un usuario eliminado (is_deleted=True)
        - No se puede desactivar la propia cuenta (is_active=False)
        - USER no puede cambiar su propio rol
        - No se puede modificar campos críticos sin permisos adecuados
        
        **Actualización completa:** Requiere enviar TODOS los campos del usuario
        ''',
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description='Usuario eliminado o datos inválidos'),
            403: OpenApiResponse(description='Permisos insuficientes'),
            404: OpenApiResponse(description='Usuario no encontrado')
        }
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente usuario (PATCH)",
        description='''
        Actualiza campos específicos de un usuario sin requerir todos los campos.
        
        **Mismas reglas y restricciones que PUT**, pero permite actualización parcial.
        
        **Ventajas:**
        - Solo enviar campos a modificar
        - Menor carga de datos
        - Ideal para actualizaciones específicas
        
        **Ejemplos comunes:**
        - Actualizar first_name/last_name
        - Cambiar email (con validación de unicidad)
        - Actualizar contraseña
        - Activar/desactivar cuenta (con restricciones)
        ''',
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description='Usuario eliminado o datos inválidos'),
            403: OpenApiResponse(description='Permisos insuficientes'),
            404: OpenApiResponse(description='Usuario no encontrado')
        },
        examples=[
            OpenApiExample(
                'Actualizar nombre',
                value={
                    'first_name': 'Updated',
                    'last_name': 'Name'
                },
                description='Actualización parcial de nombre'
            ),
            OpenApiExample(
                'Cambiar email',
                value={
                    'email': 'new.email@example.com'
                },
                description='Cambio de email (debe ser único)'
            ),
            OpenApiExample(
                'Cambiar contraseña',
                value={
                    'password': 'NewSecurePass789!'
                },
                description='Actualización de contraseña (se hashea automáticamente)'
            )
        ]
    ),
    destroy=extend_schema(
        summary="Eliminar usuario lógicamente (soft delete)",
        description='''
        Realiza borrado lógico de un usuario sin eliminarlo físicamente.
        
        **Comportamiento del soft delete:**
        1. Marca usuario como `is_deleted = True`
        2. Desactiva cuenta: `is_active = False`
        3. Mantiene registro en base de datos para integridad referencial
        4. Usuario no puede autenticarse
        
        **Jerarquía de eliminación:**
        - SUDO: Puede eliminar cualquier usuario (SUDO, ADMIN, USER)
        - ADMIN: Solo puede eliminar usuarios USER
        - USER: No puede eliminar a nadie
        
        **Restricciones críticas:**
        1. No se puede eliminar a sí mismo
        2. No se puede eliminar usuario ya eliminado
        3. No se puede eliminar usuario con nodos activos asociados
        4. Solo SUDO puede eliminar a otro SUDO
        
        **Post-eliminación:**
        - El usuario desaparece de listados (filtrado por is_deleted=False)
        - Las relaciones existentes se mantienen (integridad)
        - Se puede restaurar mediante administración directa de BD si es necesario
        ''',
        responses={
            204: OpenApiResponse(description='Usuario eliminado exitosamente'),
            400: OpenApiResponse(description='No se puede eliminar (tiene nodos activos o ya está eliminado)'),
            403: OpenApiResponse(description='Permisos insuficientes para eliminar este usuario'),
            404: OpenApiResponse(description='Usuario no encontrado')
        }
    )
)
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la gestión completa de usuarios.
    
    Sistema de roles jerárquico:
    - SUDO (Super User Ops): Acceso total, único en el sistema
    - ADMIN (Administrador): Gestión de usuarios USER y contenido
    - USER (Usuario Regular): Solo lectura y auto-gestión
    
    Características principales:
    - Autenticación JWT con validación de email confirmado
    - Permisos granulares basados en rol y acción
    - Borrado lógico (soft delete) con validaciones
    - Endpoints personalizados para perfil y auditoría
    - Filtrado, búsqueda y ordenamiento avanzado
    - Integración con app de nodos (si disponible)
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name', 'role']
    ordering_fields = ['username', 'email', 'date_joined', 'role', 'is_active']
    filterset_fields = ['role', 'is_email_confirmed', 'is_active', 'is_deleted']
    
    def get_serializer_class(self):
        """Selecciona el serializer basado en la acción."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Permisos granulares:
        - /me/: Solo usuarios activos y confirmados pueden ver su propio perfil
        - create: Solo ADMIN/SUDO pueden crear usuarios
        - list: Solo usuarios activos y confirmados pueden listar (pero la vista filtra)
        - retrieve: El propio usuario o ADMIN/SUDO pueden ver detalles
        - update/destroy: Permisos específicos según rol
        """
        if self.action == 'me':
            # Solo usuarios ACTIVOS y CONFIRMADOS pueden ver /me/
            return [IsActiveAndConfirmed()]
        
        elif self.action == 'create':
            # Solo ADMIN o SUDO pueden crear usuarios
            return [IsActiveAndConfirmed(), IsAdminUserCustom()]
        
        elif self.action == 'list':
            # Cualquier usuario activo y confirmado puede LISTAR
            # (la vista filtra qué usuarios ve según su rol)
            return [IsActiveAndConfirmed()]
        
        elif self.action == 'retrieve':
            # Para ver detalles: o es el propio usuario, o es ADMIN/SUDO
            return [IsActiveAndConfirmed(), IsOwnerOrAdmin()]
        
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Modificar/eliminar: el propio usuario o ADMIN/SUDO
            return [IsActiveAndConfirmed(), IsOwnerOrAdmin()]
        
        else:
            # Por defecto, requerir estar activo y confirmado
            return [IsActiveAndConfirmed()]
        
    def get_queryset(self):
        """
        Filtra qué usuarios son visibles según el rol:
        - SUDO: ve todos los usuarios
        - ADMIN: ve todos excepto otros SUDO
        - USER: solo ve a sí mismo
        """
        user = self.request.user
        
        if not user.is_authenticated:
            return User.objects.none()
        
        queryset = super().get_queryset()
        
        # Solo aplicar filtros para acciones de LIST y RETRIEVE
        # Para UPDATE/DELETE, necesitamos que el objeto exista para verificar permisos
        if self.action in ['list', 'retrieve']:
            if user.role == 'SUDO':
                return queryset
            elif user.role == 'ADMIN':
                return queryset.exclude(role='SUDO')
            else:  # USER
                return queryset.filter(id=user.id)
        
        # Para otras acciones (create, update, delete), devolver todos
        # Los permisos se encargarán de restringir el acceso
        return queryset

    @extend_schema(
        exclude=True  # Documentado en extend_schema_view
    )
    def create(self, request, *args, **kwargs):
        """
        Crea un nuevo usuario, validando que solo SUDO pueda crear un SUDO.
        """
        user = request.user
        
        if user.role not in ['SUDO', 'ADMIN']:
            return Response(
                {"detail": "No tienes permisos para crear usuarios."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        role = request.data.get('role', 'USER')
        if role == 'SUDO' and user.role != 'SUDO':
            return Response(
                {"role": "Solo los usuarios SUDO pueden crear otros usuarios SUDO."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)

    @extend_schema(
        exclude=True  # Documentado en extend_schema_view
    )
    def update(self, request, *args, **kwargs):
        """
        Valida que los usuarios no puedan escalar privilegios o ser editados por usuarios inferiores.
        """
        instance = self.get_object()
        user = request.user
        
        # CORRECCIÓN: Verificar que no esté eliminado
        if instance.is_deleted:
            return Response(
                {"detail": "No se puede modificar un usuario eliminado."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Regla: Un USER no puede editar a nadie más que a sí mismo
        if user.role == 'USER' and instance.pk != user.pk:
            return Response(
                {"detail": "Solo puedes actualizar tu propio perfil."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Regla: Un ADMIN no puede modificar al SUDO
        if instance.role == 'SUDO' and user.role != 'SUDO':
            return Response(
                {"detail": "No tienes permisos para modificar al usuario SUDO."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Regla: Un ADMIN no puede modificar a otro ADMIN
        if user.role == 'ADMIN' and instance.role == 'ADMIN' and instance.pk != user.pk:
            return Response(
                {"detail": "Un ADMIN no puede modificar a otro ADMIN."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validación: USER no puede cambiar su propio rol
        if user.role == 'USER' and instance.pk == user.pk and 'role' in request.data:
            return Response(
                {"role": "No puedes cambiar tu propio rol."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validación: No se puede desactivar a sí mismo
        if instance.pk == user.pk and 'is_active' in request.data and not request.data.get('is_active', True):
            return Response(
                {"is_active": "No puedes desactivar tu propia cuenta."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)

    @extend_schema(
        exclude=True  # Documentado en extend_schema_view
    )
    def destroy(self, request, *args, **kwargs):
        """
        Implementación de Borrado Lógico (Soft Delete) y validación de permisos.
        """
        instance = self.get_object()
        user = request.user
        
        # Validación: No se puede eliminar a sí mismo
        if instance.pk == user.pk:
            return Response(
                {"detail": "No puedes eliminar tu propia cuenta."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validación: No se puede eliminar un usuario ya eliminado
        if instance.is_deleted:
            return Response(
                {"detail": "Este usuario ya ha sido eliminado."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validación: Solo SUDO puede eliminar a SUDO
        if instance.role == 'SUDO' and user.role != 'SUDO':
            return Response(
                {"detail": "Solo un usuario SUDO puede eliminar a otro SUDO."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validación: Un ADMIN no puede eliminar a otro ADMIN
        if instance.role == 'ADMIN' and user.role == 'ADMIN':
            return Response(
                {"detail": "Un ADMIN no puede eliminar a otro ADMIN."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validación: USER no puede eliminar a nadie
        if user.role == 'USER':
            return Response(
                {"detail": "No tienes permisos para eliminar usuarios."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validación de Borrado Lógico (por hijos activos)
        if HAS_NODES_APP and Node is not None:
            # CORRECCIÓN: Manejo seguro de la relación
            try:
                if hasattr(instance, 'nodes_created'):
                    if instance.nodes_created.filter(is_deleted=False).exists():
                        return Response(
                            {"error": "No se puede eliminar un usuario que tiene nodos activos asociados."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                elif Node.objects.filter(created_by=instance, is_deleted=False).exists():
                    return Response(
                        {"error": "No se puede eliminar un usuario que tiene nodos activos asociados."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception:
                # Si hay error en la validación, continuar con el soft delete
                pass
        
        # Si pasa todas las validaciones, se ejecuta el soft delete
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # --- ENDPOINTS CUSTOM PARA AUDITORÍA Y PERFIL ---

    @extend_schema(
        summary="Listar nodos creados por usuario",
        description='''
        Obtiene la lista de nodos activos creados por un usuario específico.
        
        **Propósito:** Auditoría y seguimiento de actividad del usuario.
        
        **Permisos de acceso:**
        - SUDO: Puede ver nodos de cualquier usuario
        - ADMIN: Puede ver nodos de cualquier usuario (excepto SUDO)
        - USER: Solo puede ver sus propios nodos
        
        **Características:**
        - Solo incluye nodos activos (is_deleted=False)
        - Incluye relaciones anidadas (parent, created_by, updated_by)
        - Paginación automática
        - Optimizado con select_related para mejor rendimiento
        
        **Requisito:** La aplicación 'nodes' debe estar instalada y disponible.
        ''',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='ID del usuario cuyos nodos se quieren listar'
            )
        ],
        responses={
            200: NodeSerializer(many=True),
            400: OpenApiResponse(description='Usuario eliminado o datos inválidos'),
            403: OpenApiResponse(description='Permisos insuficientes'),
            404: OpenApiResponse(description='Usuario no encontrado'),
            503: OpenApiResponse(description='Aplicación de nodos no disponible')
        },
        examples=[
            OpenApiExample(
                'Respuesta exitosa',
                value=[
                    {
                        'id': 1,
                        'title': 'Nodo Principal',
                        'description': 'Descripción del nodo',
                        'created_by': {
                            'id': 2,
                            'username': 'siteadmin',
                            'email': 'admin@site.com'
                        },
                        'created_at': '2024-01-10T09:30:00Z',
                        'is_deleted': False
                    }
                ]
            )
        ]
    )
    @action(detail=True, methods=['get'], url_path='nodes-created')
    def nodes_created(self, request, pk=None):
        """Endpoint para listar nodos creados por un usuario."""
        user = self.get_object()
        # Verificar permisos: solo ADMIN/SUDO o el propio usuario
        if not (request.user.role in ['ADMIN', 'SUDO'] or request.user == user):
            return Response(
                {"detail": "No tienes permiso para ver esta información."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        nodes = user.nodes_created.filter(is_deleted=False)
        from nodes.serializers import NodeSerializer
        serializer = NodeSerializer(nodes, many=True)
        return Response(serializer.data)
    

    @extend_schema(
        summary="Obtener perfil del usuario autenticado",
        description='''
        Retorna el perfil completo del usuario actualmente autenticado.
        
        **Propósito:** Auto-gestión y acceso rápido a información personal.
        
        **Características:**
        - Incluye todos los datos del usuario
        - Métricas extendidas: nodes_created_count (si aplica)
        - Información de rol en formato legible (role_display)
        - Validación de estado del usuario (no eliminado)
        
        **Respuestas especiales:**
        - 410 GONE: Si el usuario ha sido eliminado (soft delete)
        - 401 UNAUTHORIZED: Si no hay usuario autenticado
        
        **Ejemplo de uso:** Dashboard personal, configuración de perfil
        ''',
        responses={
            200: UserDetailSerializer,
            401: OpenApiResponse(description='No autenticado'),
            410: OpenApiResponse(description='Cuenta eliminada (soft delete)')
        },
        examples=[
            OpenApiExample(
                'Perfil de usuario regular',
                value={
                    'id': 3,
                    'username': 'johndoe',
                    'email': 'john.doe@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'role': 'USER',
                    'role_display': 'Usuario Regular',
                    'is_email_confirmed': True,
                    'is_active': True,
                    'is_deleted': False,
                    'date_joined': '2024-01-03T08:00:00Z',
                    'last_login': '2024-01-13T16:45:00Z',
                    'nodes_created_count': 12
                }
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Endpoint para recuperar el perfil del usuario autenticado (GET /me)."""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "No autenticado."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # CORRECCIÓN: Verificar que el usuario no esté eliminado
        if request.user.is_deleted:
            return Response(
                {"detail": "Tu cuenta ha sido eliminada."},
                status=status.HTTP_410_GONE
            )
        
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        summary="Actualizar perfil propio",
        description='''
        Permite al usuario autenticado actualizar su propio perfil.
        
        **Características:**
        - Métodos PUT (actualización completa) y PATCH (parcial)
        - Mismas validaciones que actualización normal
        - Restricciones adicionales para auto-gestión
        
        **Restricciones específicas:**
        1. USER no puede cambiar su propio rol
        2. No se puede desactivar la propia cuenta
        3. Validación de email único (excluyéndose a sí mismo)
        4. Usuario no debe estar eliminado
        
        **Campos comúnmente actualizados:**
        - first_name, last_name
        - email (con validación de unicidad)
        - password (si se proporciona, se hashea automáticamente)
        
        **No se puede modificar:**
        - username (requeriría flujo especial)
        - role (excepto por ADMIN/SUDO)
        - is_active (para desactivar cuenta propia)
        - is_deleted (solo mediante soft delete)
        ''',
        request=UserSerializer,
        methods=['PUT', 'PATCH'],
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description='Datos inválidos'),
            401: OpenApiResponse(description='No autenticado'),
            403: OpenApiResponse(description='Restricción de auto-gestión'),
            410: OpenApiResponse(description='Cuenta eliminada')
        },
        examples=[
            OpenApiExample(
                'Actualización parcial (PATCH)',
                value={
                    'first_name': 'Jonathan',
                    'last_name': 'Smith',
                    'email': 'jonathan.smith@example.com'
                },
                description='Cambio de nombre y email'
            ),
            OpenApiExample(
                'Actualización completa (PUT)',
                value={
                    'first_name': 'Jonathan',
                    'last_name': 'Smith',
                    'email': 'jonathan.smith@example.com',
                    'password': 'NewSecurePass123!'
                },
                description='Cambio completo incluyendo contraseña'
            )
        ]
    )
    @action(detail=False, methods=['put', 'patch'], url_path='me/update')
    def update_me(self, request):
        """Endpoint para actualizar el perfil del usuario autenticado."""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "No autenticado."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # CORRECCIÓN: Verificar que el usuario no esté eliminado
        if request.user.is_deleted:
            return Response(
                {"detail": "No puedes actualizar una cuenta eliminada."},
                status=status.HTTP_410_GONE
            )
        
        partial = request.method == 'PATCH'
        serializer = UserSerializer(
            request.user, 
            data=request.data, 
            partial=partial,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Impedir que un USER cambie su propio rol
        if request.user.role == 'USER' and 'role' in request.data:
            return Response(
                {"role": "No puedes cambiar tu propio rol."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Impedir que se desactive a sí mismo
        if 'is_active' in request.data and not request.data.get('is_active', True):
            return Response(
                {"is_active": "No puedes desactivar tu propia cuenta."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        summary="Cambiar contraseña propia",
        description='''
        Permite al usuario cambiar su propia contraseña de forma segura.
        
        **Proceso de validación:**
        1. Verificar contraseña actual (old_password)
        2. Validar que nueva contraseña coincida con confirmación
        3. Verificar fortaleza de nueva contraseña (mínimo 8 caracteres)
        4. Actualizar contraseña en base de datos (hash automático)
        
        **Requisitos de contraseña:**
        - Mínimo 8 caracteres
        - Se recomienda usar mayúsculas, minúsculas, números y símbolos
        - No se almacena en texto plano (siempre hasheada)
        
        **Consideraciones de seguridad:**
        - Usuario debe estar autenticado
        - Usuario no debe estar eliminado
        - Después del cambio, tokens JWT existentes siguen válidos hasta expiración
        - Para invalidar todas las sesiones, se requiere logout manual
        
        **Respuestas de error específicas:**
        - 400: Contraseña actual incorrecta o no coinciden
        - 401: No autenticado
        - 410: Cuenta eliminada
        ''',
        request={
            'application/json': {
                'type': 'object',
                'required': ['old_password', 'new_password', 'confirm_password'],
                'properties': {
                    'old_password': {
                        'type': 'string',
                        'format': 'password',
                        'description': 'Contraseña actual del usuario',
                        'minLength': 1
                    },
                    'new_password': {
                        'type': 'string',
                        'format': 'password',
                        'description': 'Nueva contraseña (mínimo 8 caracteres)',
                        'minLength': 8
                    },
                    'confirm_password': {
                        'type': 'string',
                        'format': 'password',
                        'description': 'Confirmación de nueva contraseña',
                        'minLength': 8
                    }
                },
                'example': {
                    'old_password': 'CurrentPass123',
                    'new_password': 'NewSecurePass456!',
                    'confirm_password': 'NewSecurePass456!'
                }
            }
        },
        responses={
            200: OpenApiResponse(
                description='Contraseña actualizada correctamente',
                examples=[
                    OpenApiExample(
                        'Respuesta exitosa',
                        value={'detail': 'Contraseña actualizada correctamente.'}
                    )
                ]
            ),
            400: OpenApiResponse(
                description='Error de validación',
                examples=[
                    OpenApiExample(
                        'Contraseña actual incorrecta',
                        value={'old_password': 'Contraseña actual incorrecta.'}
                    ),
                    OpenApiExample(
                        'Contraseñas no coinciden',
                        value={'confirm_password': 'Las contraseñas no coinciden.'}
                    ),
                    OpenApiExample(
                        'Contraseña muy corta',
                        value={'new_password': 'La contraseña debe tener al menos 8 caracteres.'}
                    )
                ]
            ),
            401: OpenApiResponse(description='No autenticado'),
            410: OpenApiResponse(description='Cuenta eliminada')
        }
    )
    @action(detail=False, methods=['post'], url_path='me/change-password')
    def change_password(self, request):
        """Endpoint para que el usuario actual cambie su propia contraseña."""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "No autenticado."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # CORRECCIÓN: Verificar que el usuario no esté eliminado
        if request.user.is_deleted:
            return Response(
                {"detail": "No puedes cambiar la contraseña de una cuenta eliminada."},
                status=status.HTTP_410_GONE
            )
        
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not all([old_password, new_password, confirm_password]):
            return Response(
                {"detail": "Todos los campos son requeridos."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_password != confirm_password:
            return Response(
                {"confirm_password": "Las contraseñas no coinciden."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not request.user.check_password(old_password):
            return Response(
                {"old_password": "Contraseña actual incorrecta."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(new_password) < 8:
            return Response(
                {"new_password": "La contraseña debe tener al menos 8 caracteres."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        request.user.set_password(new_password)
        request.user.save()
        
        return Response({"detail": "Contraseña actualizada correctamente."})


# ============================================================================
# CONFIGURACIÓN GLOBAL PARA DOCUMENTACIÓN
# ============================================================================
UserViewSetDocumentationConfig = {
    'tags': ['users'],
    'operation_id_prefix': 'users_',
    'description': '''
    ## Sistema Completo de Gestión de Usuarios
    
    **Arquitectura de roles:**
    ```
    SUDO (Super User Ops) → ADMIN (Administrador) → USER (Usuario Regular)
    ```
    
    **Características principales:**
    1. **Autenticación JWT** con validación de email confirmado
    2. **Jerarquía estricta** de permisos basada en roles
    3. **Borrado lógico** (soft delete) con validaciones de integridad
    4. **Auto-gestión** completa con endpoints /me/*
    5. **Auditoría** de actividad (nodos creados)
    6. **Filtrado avanzado** por múltiples criterios
    
    **Flujos comunes:**
    - Registro → Confirmación email → Login → Operaciones según rol
    - Creación usuarios → Asignación roles → Gestión permisos
    - Auto-gestión → Cambio datos → Cambio contraseña
    
    **Integraciones:**
    - Panel de administración Django (SUDO/ADMIN)
    - Aplicación de nodos (auditoría de actividad)
    - Sistema de permisos personalizado
    '''
}