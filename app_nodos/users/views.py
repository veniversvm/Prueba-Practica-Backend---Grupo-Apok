from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from nodes.serializers import NodeSerializer 
from .models import User
from .serializers import UserSerializer, UserDetailSerializer, UserCreateSerializer
from .permissions import IsActiveAndConfirmed, IsAdminUserCustom, IsSudoUser 

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la gestión completa de usuarios.

    Implementa control de acceso basado en roles (SUDO, ADMIN, USER) para CRUD,
    validaciones estrictas de creación/actualización de roles,
    y endpoints custom para auditoría de nodos y gestión de perfil.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'date_joined', 'role', 'is_active']
    filterset_fields = ['role', 'is_email_confirmed', 'is_active']
    
    def get_serializer_class(self):
        """Selecciona el serializer basado en la acción (Create, Retrieve, List/Update)."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer

    def get_permissions(self):
        """Define la política de permisos granular basada en la acción de la API."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUserCustom]
        elif self.action == 'list':
            permission_classes = [IsActiveAndConfirmed]
        else:
            permission_classes = [IsActiveAndConfirmed]
        
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Aplica filtros al queryset basados en el rol del usuario (Seguridad a nivel de DB)."""
        user = self.request.user
        
        if not user.is_authenticated:
            return User.objects.none()
        
        if user.role == 'SUDO':
            # SUDO ve todos los usuarios
            return User.objects.all()
        elif user.role == 'ADMIN':
            # ADMIN ve todos excepto el SUDO principal
            return User.objects.exclude(role='SUDO')
        else:  # USER
            # USER solo puede ver su propio perfil
            return User.objects.filter(pk=user.pk)

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

    def update(self, request, *args, **kwargs):
        """
        Valida que los usuarios no puedan escalar privilegios o ser editados por usuarios inferiores.
        """
        instance = self.get_object()
        user = request.user
        
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
        
        # Validación: USER no puede cambiar su propio rol
        if user.role == 'USER' and instance.pk == user.pk and 'role' in request.data:
            return Response(
                {"role": "No puedes cambiar tu propio rol."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Implementación de Borrado Lógico (Soft Delete) y validación de permisos.
        """
        instance = self.get_object()
        user = request.user
        
        # Validación de Borrado Lógico (por hijos activos del modelo Node)
        if instance.children.filter(is_deleted=False).exists():
            return Response(
                {"error": "No se puede eliminar un nodo que tiene hijos activos."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validación de Permisos de Borrado
        if user.role == 'USER':
            return Response(
                {"detail": "No tienes permisos para eliminar recursos."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # ADMIN solo puede borrar USERs
        if user.role == 'ADMIN' and instance.role in ['ADMIN', 'SUDO']:
            return Response(
                {"detail": "Solo puedes eliminar usuarios con rol USER."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Si pasa todas las validaciones, se ejecuta el soft delete
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # --- ENDPOINTS CUSTOM PARA AUDITORÍA Y PERFIL ---

    @action(detail=True, methods=['get'], url_path='nodes-created')
    def nodes_created(self, request, pk=None):
        """
        Endpoint custom para listar los nodos CREADOS por un usuario específico.
        Permite a ADMIN/SUDO ver todos; USER solo puede ver los suyos.
        """
        user = self.get_object()
        requesting_user = request.user
        
        # Seguridad: Un USER solo puede ver los nodos creados por él mismo.
        if requesting_user.role == 'USER' and requesting_user.pk != user.pk:
            return Response(
                {"detail": "No tienes permisos para ver los nodos creados por este usuario."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Filtrar nodos creados por el usuario (solo activos)
        nodes = Node.objects.filter(
            created_by=user,
            is_deleted=False
        ).select_related('parent', 'created_by', 'updated_by')
        
        page = self.paginate_queryset(nodes)
        if page is not None:
            serializer = NodeSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = NodeSerializer(nodes, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Endpoint para recuperar el perfil del usuario autenticado (GET /me)."""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "No autenticado."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'], url_path='me/update')
    def update_me(self, request):
        """Endpoint para actualizar el perfil del usuario autenticado."""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "No autenticado."},
                status=status.HTTP_401_UNAUTHORIZED
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
        
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='me/change-password')
    def change_password(self, request):
        """Endpoint para que el usuario actual cambie su propia contraseña."""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "No autenticado."},
                status=status.HTTP_401_UNAUTHORIZED
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
        
        request.user.set_password(new_password)
        request.user.save()
        
        return Response({"detail": "Contraseña actualizada correctamente."})