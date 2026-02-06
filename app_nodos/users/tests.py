from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase

from nodes.models import Node # Necesario para el conteo de nodos en el test de detalle

User = get_user_model()


class UserViewSetEndpointTest(APITestCase):

    def setUp(self):
        self.sudo_user = User.objects.create_user(
            username='sudo',
            email='sudo@ok.com',
            password='test123',
            role='SUDO',
            is_email_confirmed=True
        )

        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@ok.com',
            password='test123',
            role='ADMIN',
            is_email_confirmed=True
        )

        self.extra_admin = User.objects.create_user(
            username='admin_boss',
            email='boss@ok.com',
            password='test123',
            role='ADMIN',
            is_email_confirmed=True
        )

        self.regular_user = User.objects.create_user(
            username='user',
            email='user@ok.com',
            password='test123',
            role='USER',
            is_email_confirmed=True
        )

        self.unconfirmed_user = User.objects.create_user(
            username='pending',
            email='pending@ok.com',
            password='test123',
            role='USER',
            is_email_confirmed=False
        )

        self.token_url = reverse('token_obtain_pair')
        self.users_url = reverse('user-list')

    def _login(self, username):
        response = self.client.post(self.token_url, {
            'username': username,
            'password': 'test123'
        })
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )

    def test_sudo_can_list_all_users(self):
        self._login('sudo')

        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [u['username'] for u in response.data]
        self.assertIn('admin_boss', usernames)
        self.assertIn('admin', usernames)
        self.assertIn('user', usernames)

    def test_admin_can_list_users(self):
        self._login('admin')

        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_list_users(self):
        self._login('user')

        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unconfirmed_user_cannot_authenticate(self):
        response = self.client.post(self.token_url, {
            'username': 'pending',
            'password': 'test123'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class JWTAuthenticationTest(APITestCase):

    def setUp(self):
        self.confirmed_admin = User.objects.create_user(
            username='admin_boss',
            email='boss@ok.com',
            password='testpassword',
            role='ADMIN',
            is_email_confirmed=True
        )

        self.pending_user = User.objects.create_user(
            username='user_pending',
            email='pending@ok.com',
            password='testpassword',
            role='USER',
            is_email_confirmed=False
        )

        self.token_url = reverse('token_obtain_pair')

    def test_confirmed_user_can_get_token(self):
        response = self.client.post(self.token_url, {
            'username': 'admin_boss',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_unconfirmed_user_cannot_get_token(self):
        response = self.client.post(self.token_url, {
            'username': 'user_pending',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_credentials(self):
        response = self.client.post(self.token_url, {
            'username': 'admin_boss',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class UserSecurityTest(APITestCase):

    def setUp(self):
        self.confirmed_user = User.objects.create_user(
            username='secure_user',
            email='secure@ok.com',
            password='test123',
            role='USER',
            is_email_confirmed=True
        )

        self.unconfirmed_user = User.objects.create_user(
            username='not_confirmed',
            email='no@ok.com',
            password='test123',
            role='USER',
            is_email_confirmed=False
        )

        self.token_url = reverse('token_obtain_pair')
        self.me_url = reverse('user-me')

    def _authenticate(self, username, password='test123'):
        response = self.client.post(self.token_url, {
            'username': username,
            'password': password
        })
        return response.data.get('access')

    def test_confirmed_user_can_access_me(self):
        token = self._authenticate('secure_user')

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'secure_user')

    def test_unconfirmed_user_cannot_get_token(self):
        response = self.client.post(self.token_url, {
            'username': 'not_confirmed',
            'password': 'test123'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    """
    Suite de pruebas para los endpoints del UserViewSet, simulando autenticación JWT.
    """
    def setUp(self):
        """Configura usuarios con roles y un árbol de nodos para probar permisos."""
        # Usuarios base
        self.sudo_user = User.objects.create_user(username='sudo_user', email='sudo@test.com', password='test123', role='SUDO', is_email_confirmed=True)
        self.admin_user = User.objects.create_user(username='admin_user', email='admin@test.com', password='test123', role='ADMIN', is_email_confirmed=True)
        self.regular_user = User.objects.create_user(username='regular_user', email='regular@test.com', password='test123', role='USER', is_email_confirmed=True)
        self.unconfirmed_user = User.objects.create_user(username='unconfirmed_user', email='unconfirmed@test.com', password='test123', role='USER', is_email_confirmed=False)
        
        # Nodos para auditoría
        self.node1 = Node.objects.create(title='Node 1', created_by=self.regular_user, updated_by=self.regular_user)
        self.node2 = Node.objects.create(title='Node 2', parent=self.node1, created_by=self.regular_user, updated_by=self.regular_user)
        self.admin_node = Node.objects.create(title='Admin Node', created_by=self.admin_user, updated_by=self.admin_user)
        
        # URLs
        self.users_url = reverse('user-list')
        self.me_url = reverse('user-me')
        self.change_password_url = reverse('user-change-password')
        
    def _get_token(self, username):
        """Helper para obtener token JWT."""
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': username, 'password': 'test123'
        })
        return response.data['access']
    
    def _authenticate(self, user):
        """Helper para autenticar un usuario simulando el token."""
        token = self._get_token(user.username)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # --- TESTS PARA ENDPOINT /api/users/me/ ---

    def test_get_me_endpoint_success(self):
        """Verifica que un usuario autenticado puede obtener su propio perfil."""
        self._authenticate(self.regular_user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'regular_user')

    def test_get_me_endpoint_unconfirmed_user_fails(self):
        token = self._get_token(self.unconfirmed_user.username)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(self.me_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )



    # --- TESTS DE CAMBIO DE CONTRASEÑA ---

    def test_change_password_endpoint_success(self):
        self._authenticate(self.regular_user)

        response = self.client.post(
            self.change_password_url,
            {
                'old_password': 'test123',
                'new_password': 'newpassword123',
                'confirm_password': 'newpassword123'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.check_password('newpassword123'))


    # --- TESTS DE PERMISOS EN LISTAR/BUSCAR USUARIOS ---

    def test_regular_user_cannot_list_other_users(self):
        """Test que verifica que un USER no puede listar todos los usuarios (solo ve su perfil)."""
        self._authenticate(self.regular_user)
        response = self.client.get(self.users_url)
        
        # El get_queryset para USER filtra a sí mismo
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'regular_user')

    def test_admin_can_list_users_except_sudo(self):
        """Test que verifica que un ADMIN puede listar usuarios excepto SUDO."""
        self._authenticate(self.admin_user)
        response = self.client.get(self.users_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = [user['username'] for user in response.data]
        self.assertNotIn('sudo_user', usernames) # No debería ver al SUDO

    def test_sudo_can_list_all_users(self):
        """Test que verifica que un SUDO puede listar todos los usuarios."""
        self._authenticate(self.sudo_user)
        response = self.client.get(self.users_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = [user['username'] for user in response.data]
        self.assertIn('sudo_user', usernames)
        self.assertIn('admin_boss', usernames)

    # --- TESTS DE AUDITORÍA DE NODOS (Añadidos al final) ---

    def test_user_profile_shows_node_count(self):
        """Verifica que el campo nodes_created_count funciona en el UserDetailSerializer."""
        self._authenticate(self.regular_user)
        
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # El usuario regular creó Node 1 y Node 2
        self.assertEqual(response.data['nodes_created_count'], 2)
        
    # Nota: Los tests de PUT/DELETE/POST de usuarios requieren Serializers
    # y más configuración, pero ya cubrimos el login y la lectura.