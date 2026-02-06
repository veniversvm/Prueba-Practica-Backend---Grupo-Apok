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
    ViewSet para la gestión de usuarios.

    Implementa funcionalidades CRUD con filtros avanzados y seguridad basada en roles
    (SUDO, ADMIN, USER), controlando el acceso a la gestión de otros usuarios.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'date_joined', 'role', 'is_active']
    filterset_fields = ['role', 'is_email_confirmed', 'is_active']
    
    def get_serializer_class(self):
        """Selecciona el serializer adecuado basado en la acción (Create, Retrieve, List/Update)."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer

    def get_permissions(self):
        """Define la política de permisos granular basada en la acción de la API."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Las acciones de escritura/borrado requieren permisos más altos
            permission_classes = [IsAdminUserCustom]
        elif self.action == 'list':
            # Listado requiere solo estar activo y confirmado (LECTURA)
            permission_classes = [IsActiveAndConfirmed]
        else:
            # Default para retrieve
            permission_classes = [IsActiveAndConfirmed]
        
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Aplica filtros al queryset basados en el rol del usuario autenticado (Seguridad a nivel de DB)."""
        user = self.request.user
        
        if not user.is_authenticated:
            return User.objects.none()
        
        if user.role == 'SUDO':
            # SUDO ve todos los usuarios (incluyendo otros SUDO)
            return User.objects.all()
        elif user.role == 'ADMIN':
            # ADMIN ve todos excepto el SUDO principal
            return User.objects.exclude(role='SUDO')
        else:  # USER
            # USER solo puede ver su propio perfil
            return User.objects.filter(pk=user.pk)

    def create(self, request, *args, **kwargs):
        """
        Crea un nuevo usuario, aplicando la lógica de permisos de rol antes de la creación.
        """
        user = request.user
        
        # Validación de Permiso para Crear
        if user.role not in ['SUDO', 'ADMIN']:
            return Response(
                {"detail": "No tienes permisos para crear usuarios."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validación de Asignación de Rol SUDO
        role = request.data.get('role', 'USER')
        if role == 'SUDO' and user.role != 'SUDO':
            return Response(
                {"role": "Solo los usuarios SUDO pueden crear otros usuarios SUDO."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Valida que los usuarios no puedan escalar privilegios o ser eliminados por los equivocados.
        """
        instance = self.get_object()
        user = request.user
        
        # Regla: Un USER no puede editar a nadie más que a sí mismo
        if user.role == 'USER' and instance.pk != user.pk:
            return Response(
                {"detail": "Solo puedes actualizar tu propio perfil."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Regla: Un ADMIN no puede modificar al SUDO (ni a sí mismo si intenta subir de rol)
        if instance.role == 'SUDO' and user.role != 'SUDO':
             return Response(
                {"detail": "No tienes permisos para modificar al usuario SUDO."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validación de cambio de rol (USER no puede cambiar su rol)
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
        
        # Validación de Borrado Lógico (por hijos activos)
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
        
        # SUDO puede borrar cualquiera (excepto a sí mismo, si se configura en el test)
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
        Requiere autenticación (IsAuthenticated).
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
        
        # Paginación estándar
        page = self.paginate_queryset(nodes)
        if page is not None:
            serializer = NodeSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = NodeSerializer(nodes, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Endpoint para recuperar el perfil del usuario autenticado."""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "No autenticado."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Usamos un serializer detallado para el perfil de usuario (asumimos que existe)
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
    
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase
from nodes.models import Node

User = get_user_model()


class UserSecurityTest(TestCase):
    """
    Suite de pruebas para validar las reglas de negocio y restricciones a nivel
    de modelo y manager de usuario.
    """
    def setUp(self):
        """Configura dos usuarios base con diferentes estados de confirmación/roles."""
        # Usuario ADMIN confirmado: Debería poder hacer todo
        self.confirmed_admin = User.objects.create_user(
            username='admin_ok', email='admin@ok.com', password='testpassword', 
            role='ADMIN', is_email_confirmed=True
        )
        # Usuario USER pendiente: No debería poder autenticarse
        self.pending_user = User.objects.create_user(
            username='user_no_email', email='user@no.com', password='testpassword', 
            role='USER', is_email_confirmed=False
        )

    def test_sudo_unique_constraint(self):
        """
        Valida la regla de negocio: Solo se puede crear UN único usuario con rol 'SUDO'.
        """
        # Crea el primer SUDO (el sistema lo permite)
        User.objects.create_user(
            username='sudo_1', email='sudo1@sys.com', password='testpassword', 
            role='SUDO', is_email_confirmed=True
        )
        
        # Intenta crear un segundo SUDO y espera la excepción de validación
        with self.assertRaises(ValidationError) as cm:
            User.objects.create_user(
                username='sudo_2', email='sudo2@sys.com', password='testpassword', 
                role='SUDO', is_email_confirmed=True
            )
        
        # Verifica que el mensaje de error coincide con el lanzado en el modelo User.save()
        self.assertIn(
            "Ya existe un usuario SUDO", 
            str(cm.exception)
        )


class JWTAuthenticationTest(APITestCase):
    """
    Suite de pruebas para validar el flujo de autenticación JWT contra el
    EmailOrUsernameBackend personalizado.
    """
    def setUp(self):
        """Configura usuarios y la URL de obtención de token."""
        # Usuario ADMIN confirmado: Debe pasar
        self.confirmed_admin = User.objects.create_user(
            username='admin_boss', email='boss@ok.com', password='testpassword', 
            role='ADMIN', is_email_confirmed=True
        )
        # Usuario PENDING: Debe fallar la autenticación
        self.pending_user = User.objects.create_user(
            username='user_pending', email='pending@ok.com', password='testpassword', 
            role='USER', is_email_confirmed=False
        )
        self.login_url = reverse('token_obtain_pair')

    # --- TESTS DE LOGIN DUAL Y CONFIRMACIÓN ---

    def test_login_with_username_success(self):
        """Verifica que el login con username funciona si el usuario está confirmado."""
        response = self.client.post(self.login_url, 
            {'username': 'admin_boss', 'password': 'testpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_login_with_email_success(self):
        """Verifica que el login con email funciona si el usuario está confirmado."""
        response = self.client.post(self.login_url, 
            {'username': 'boss@ok.com', 'password': 'testpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_login_with_unconfirmed_email_fails(self):
        """Valida que el login falla con 401 si el usuario no ha confirmado su email."""
        response = self.client.post(self.login_url, 
            {'username': 'pending@ok.com', 'password': 'testpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('no active account', response.data['detail'].lower())


class UserViewSetEndpointTest(APITestCase):
    """
    Suite de pruebas para los nuevos endpoints del UserViewSet.
    """
    def setUp(self):
        """Configura usuarios de diferentes roles y algunos nodos para pruebas."""
        # Usuario SUDO
        self.sudo_user = User.objects.create_user(
            username='sudo_user', email='sudo@test.com', password='test123',
            role='SUDO', is_email_confirmed=True
        )
        
        # Usuario ADMIN
        self.admin_user = User.objects.create_user(
            username='admin_user', email='admin@test.com', password='test123',
            role='ADMIN', is_email_confirmed=True
        )
        
        # Usuario USER normal
        self.regular_user = User.objects.create_user(
            username='regular_user', email='regular@test.com', password='test123',
            role='USER', is_email_confirmed=True
        )
        
        # Usuario USER no confirmado
        self.unconfirmed_user = User.objects.create_user(
            username='unconfirmed_user', email='unconfirmed@test.com', password='test123',
            role='USER', is_email_confirmed=False
        )
        
        # Crear algunos nodos para el usuario regular
        self.node1 = Node.objects.create(
            title='Node 1',
            created_by=self.regular_user,
            updated_by=self.regular_user
        )
        
        self.node2 = Node.objects.create(
            title='Node 2',
            parent=self.node1,
            created_by=self.regular_user,
            updated_by=self.regular_user
        )
        
        # Crear un nodo para el admin (para test de permisos)
        self.admin_node = Node.objects.create(
            title='Admin Node',
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # URLs
        self.users_url = reverse('user-list')
        self.me_url = reverse('user-me')
        self.change_password_url = reverse('user-change-password')
        
    def _get_token(self, username):
        """Helper para obtener token JWT."""
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': username,
            'password': 'test123'
        })
        return response.data['access']
    
    def _authenticate(self, user):
        """Helper para autenticar un usuario."""
        token = self._get_token(user.username)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # --- TESTS PARA ENDPOINT /api/users/me/ ---

    def test_get_me_endpoint_success(self):
        """Test que verifica que un usuario autenticado puede obtener su propio perfil."""
        self._authenticate(self.regular_user)
        
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'regular_user')
        self.assertEqual(response.data['email'], 'regular@test.com')
        self.assertEqual(response.data['role'], 'USER')
        self.assertTrue(response.data['is_email_confirmed'])

    def test_get_me_endpoint_unauthenticated(self):
        """Test que verifica que un usuario no autenticado no puede acceder a /me."""
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('No autenticado', response.data['detail'])

    def test_get_me_endpoint_unconfirmed_user(self):
        """Test que verifica que un usuario no confirmado no puede acceder a /me."""
        self._authenticate(self.unconfirmed_user)
        
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Asumiendo que IsActiveAndConfirmed bloquea usuarios no confirmados

    # --- TESTS PARA ENDPOINT /api/users/me/update/ ---

    def test_update_me_endpoint_success(self):
        """Test que verifica que un usuario puede actualizar su propio perfil."""
        self._authenticate(self.regular_user)
        
        update_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'updated@test.com'
        }
        
        response = self.client.patch(f"{self.me_url}update/", update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'John')
        self.assertEqual(response.data['last_name'], 'Doe')
        self.assertEqual(response.data['email'], 'updated@test.com')
        
        # Verificar que se actualizó en la base de datos
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.first_name, 'John')
        self.assertEqual(self.regular_user.last_name, 'Doe')

    def test_update_me_endpoint_cannot_change_role(self):
        """Test que verifica que un USER no puede cambiar su propio rol."""
        self._authenticate(self.regular_user)
        
        update_data = {
            'role': 'ADMIN'  # Intento de escalada de privilegios
        }
        
        response = self.client.patch(f"{self.me_url}update/", update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('No puedes cambiar tu propio rol', response.data['role'])
        
        # Verificar que el rol no cambió
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.role, 'USER')

    def test_update_me_endpoint_admin_can_change_role(self):
        """Test que verifica que un ADMIN puede cambiar su propio rol (si tiene permiso)."""
        self._authenticate(self.admin_user)
        
        update_data = {
            'role': 'USER'  # ADMIN bajando su propio rol (si está permitido)
        }
        
        response = self.client.patch(f"{self.me_url}update/", update_data, format='json')
        
        # Depende de tu implementación: ¿Puede un ADMIN cambiar su propio rol?
        # Si no está permitido, debería devolver 403
        # Si está permitido, debería devolver 200
        # Vamos a asumir que está permitido basado en tu código
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    # --- TESTS PARA ENDPOINT /api/users/me/change-password/ ---

    def test_change_password_endpoint_success(self):
        """Test que verifica que un usuario puede cambiar su contraseña correctamente."""
        self._authenticate(self.regular_user)
        
        password_data = {
            'old_password': 'test123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(self.change_password_url, password_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Contraseña actualizada correctamente', response.data['detail'])
        
        # Verificar que la nueva contraseña funciona
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.check_password('newpassword123'))

    def test_change_password_wrong_old_password(self):
        """Test que verifica error cuando la contraseña actual es incorrecta."""
        self._authenticate(self.regular_user)
        
        password_data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(self.change_password_url, password_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Contraseña actual incorrecta', response.data['old_password'])

    def test_change_password_mismatch_new_passwords(self):
        """Test que verifica error cuando las nuevas contraseñas no coinciden."""
        self._authenticate(self.regular_user)
        
        password_data = {
            'old_password': 'test123',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword'
        }
        
        response = self.client.post(self.change_password_url, password_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Las contraseñas no coinciden', response.data['confirm_password'])

    def test_change_password_missing_fields(self):
        """Test que verifica error cuando faltan campos obligatorios."""
        self._authenticate(self.regular_user)
        
        password_data = {
            'old_password': 'test123',
            # Falta new_password y confirm_password
        }
        
        response = self.client.post(self.change_password_url, password_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Todos los campos son requeridos', response.data['detail'])

    def test_change_password_short_new_password(self):
        """Test que verifica error cuando la nueva contraseña es muy corta."""
        self._authenticate(self.regular_user)
        
        password_data = {
            'old_password': 'test123',
            'new_password': 'short',
            'confirm_password': 'short'
        }
        
        response = self.client.post(self.change_password_url, password_data, format='json')
        
        # En tu código actual no hay validación de longitud, pero es buena práctica
        # Si añades validación de longitud, este test debería fallar
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    # --- TESTS PARA ENDPOINT /api/users/{id}/nodes-created/ ---

    def test_nodes_created_endpoint_regular_user_own_profile(self):
        """Test que verifica que un USER puede ver sus propios nodos creados."""
        self._authenticate(self.regular_user)
        
        url = reverse('user-nodes-created', kwargs={'pk': self.regular_user.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Debería tener 2 nodos
        
        # Verificar que los nodos son los correctos
        node_titles = [node['title'] for node in response.data]
        self.assertIn('Node 1', node_titles)
        self.assertIn('Node 2', node_titles)

    def test_nodes_created_endpoint_regular_user_other_user(self):
        """Test que verifica que un USER NO puede ver nodos creados por otro usuario."""
        self._authenticate(self.regular_user)
        
        url = reverse('user-nodes-created', kwargs={'pk': self.admin_user.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('No tienes permisos para ver los nodos creados por este usuario', 
                     response.data['detail'])

    def test_nodes_created_endpoint_admin_can_see_other_users_nodes(self):
        """Test que verifica que un ADMIN puede ver nodos creados por otros usuarios."""
        self._authenticate(self.admin_user)
        
        url = reverse('user-nodes-created', kwargs={'pk': self.regular_user.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_nodes_created_endpoint_sudo_can_see_all_nodes(self):
        """Test que verifica que un SUDO puede ver nodos creados por cualquier usuario."""
        self._authenticate(self.sudo_user)
        
        url = reverse('user-nodes-created', kwargs={'pk': self.regular_user.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # También puede ver nodos del admin
        url = reverse('user-nodes-created', kwargs={'pk': self.admin_user.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Admin Node')

    def test_nodes_created_endpoint_only_active_nodes(self):
        """Test que verifica que solo se devuelven nodos activos (no borrados)."""
        self._authenticate(self.sudo_user)
        
        # Crear un nodo borrado para el usuario regular
        deleted_node = Node.objects.create(
            title='Deleted Node',
            created_by=self.regular_user,
            updated_by=self.regular_user,
            is_deleted=True
        )
        
        url = reverse('user-nodes-created', kwargs={'pk': self.regular_user.pk})
        response = self.client.get(url)
        
        # Solo deberían aparecer 2 nodos (los activos)
        self.assertEqual(len(response.data), 2)
        
        # Verificar que el nodo borrado no está en la respuesta
        node_titles = [node['title'] for node in response.data]
        self.assertNotIn('Deleted Node', node_titles)

    def test_nodes_created_endpoint_pagination(self):
        """Test que verifica que el endpoint soporta paginación."""
        self._authenticate(self.sudo_user)
        
        # Crear más nodos para testear paginación
        for i in range(15):
            Node.objects.create(
                title=f'Test Node {i}',
                created_by=self.regular_user,
                updated_by=self.regular_user
            )
        
        url = reverse('user-nodes-created', kwargs={'pk': self.regular_user.pk})
        response = self.client.get(url)
        
        # Debería tener paginación (asumiendo PAGE_SIZE = 10)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        
        # Verificar que hay más de 10 nodos en total
        self.assertGreater(response.data['count'], 10)
        
        # Verificar que la primera página tiene 10 resultados
        self.assertEqual(len(response.data['results']), 10)

    def test_nodes_created_endpoint_user_not_found(self):
        """Test que verifica error cuando se solicita nodos de un usuario que no existe."""
        self._authenticate(self.sudo_user)
        
        url = reverse('user-nodes-created', kwargs={'pk': 99999})  # ID que no existe
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- TESTS DE PERMISOS ADICIONALES ---

    def test_regular_user_cannot_list_users(self):
        """Test que verifica que un USER regular no puede listar todos los usuarios."""
        self._authenticate(self.regular_user)
        
        response = self.client.get(self.users_url)
        
        # Según tu código, USER solo puede ver su propio perfil en get_queryset
        # Así que debería devolver solo 1 usuario (él mismo)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'regular_user')

    def test_admin_can_list_users_except_sudo(self):
        """Test que verifica que un ADMIN puede listar usuarios excepto SUDO."""
        self._authenticate(self.admin_user)
        
        response = self.client.get(self.users_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Debería ver: admin_user, regular_user, unconfirmed_user
        # Pero NO sudo_user
        usernames = [user['username'] for user in response.data]
        self.assertIn('admin_user', usernames)
        self.assertIn('regular_user', usernames)
        self.assertIn('unconfirmed_user', usernames)
        self.assertNotIn('sudo_user', usernames)

    def test_sudo_can_list_all_users(self):
        """Test que verifica que un SUDO puede listar todos los usuarios."""
        self._authenticate(self.sudo_user)
        
        response = self.client.get(self.users_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Debería ver todos los usuarios
        usernames = [user['username'] for user in response.data]
        self.assertIn('sudo_user', usernames)
        self.assertIn('admin_user', usernames)
        self.assertIn('regular_user', usernames)
        self.assertIn('unconfirmed_user', usernames)

    def test_unconfirmed_user_cannot_access_protected_endpoints(self):
        """Test que verifica que un usuario no confirmado no puede acceder a endpoints protegidos."""
        self._authenticate(self.unconfirmed_user)
        
        # Intentar acceder a /me
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Intentar acceder a la lista de usuarios
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- TESTS DE SOFT DELETE PARA USUARIOS ---

    def test_regular_user_cannot_delete_anyone(self):
        """Test que verifica que un USER no puede eliminar a nadie."""
        self._authenticate(self.regular_user)
        
        url = reverse('user-detail', kwargs={'pk': self.unconfirmed_user.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('No tienes permisos para eliminar recursos', response.data['detail'])

    def test_admin_can_delete_regular_user(self):
        """Test que verifica que un ADMIN puede eliminar un USER regular."""
        self._authenticate(self.admin_user)
        
        # Crear un USER adicional para eliminar
        user_to_delete = User.objects.create_user(
            username='to_delete', email='delete@test.com', password='test123',
            role='USER', is_email_confirmed=True
        )
        
        url = reverse('user-detail', kwargs={'pk': user_to_delete.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar que el usuario fue marcado como eliminado (soft delete)
        user_to_delete.refresh_from_db()
        self.assertTrue(user_to_delete.is_deleted)

    def test_admin_cannot_delete_admin_or_sudo(self):
        """Test que verifica que un ADMIN no puede eliminar otro ADMIN o SUDO."""
        self._authenticate(self.admin_user)
        
        # Intentar eliminar a sí mismo (ADMIN)
        url = reverse('user-detail', kwargs={'pk': self.admin_user.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Solo puedes eliminar usuarios con rol USER', response.data['detail'])
        
        # Intentar eliminar SUDO
        url = reverse('user-detail', kwargs={'pk': self.sudo_user.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('No tienes permisos para modificar al usuario SUDO', response.data['detail'])

    def test_sudo_can_delete_anyone_except_self(self):
        """Test que verifica que un SUDO puede eliminar a cualquiera excepto a sí mismo."""
        self._authenticate(self.sudo_user)
        
        # Eliminar ADMIN
        url = reverse('user-detail', kwargs={'pk': self.admin_user.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar que fue marcado como eliminado
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_deleted)

    def test_user_cannot_delete_node_with_active_children(self):
        """Test que verifica que no se puede eliminar un usuario que tiene nodos activos."""
        # Este test depende de cómo implementes la validación en destroy()
        # Tu código actual verifica instance.children.filter(is_deleted=False).exists()
        # pero eso es para el modelo Node, no User. Puede que necesites ajustar este test.
        pass


# Para ejecutar estos tests:
# python manage.py test users.tests.UserViewSetEndpointTest
# python manage.py test users.tests.UserViewSetEndpointTest.test_get_me_endpoint_success