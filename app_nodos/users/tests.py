from django.test import TestCase, TransactionTestCase # Importar TransactionTestCase para tests de modelo si es necesario
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase
from nodes.models import Node # Necesario para el conteo de nodos

User = get_user_model()


# --- TEST DE MODELO / LÓGICA DE USUARIO (Usa TestCase) ---
class UserSecurityTest(TestCase):
    """Prueba las reglas de negocio a nivel de modelo (SUDO único, ValidationError)."""
    
    def setUp(self):
        """Configura usuarios base para testear reglas de modelo."""
        # Se crea el primer SUDO que usará el sistema
        User.objects.create_user(
            username='sudo_1', email='sudo1@sys.com', password='testpassword', 
            role='SUDO', is_email_confirmed=True
        )
        # Se crea un usuario confirmado para otros tests si fueran necesarios
        User.objects.create_user(
            username='admin_ok', email='admin@ok.com', password='testpassword', 
            role='ADMIN', is_email_confirmed=True
        )

    def test_sudo_unique_constraint(self):
        """Valida que la creación de un segundo SUDO lanza ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            User.objects.create_user(
                username='sudo_2', email='sudo2@sys.com', password='testpassword', 
                role='SUDO', is_email_confirmed=True
            )
        self.assertIn("Ya existe un usuario SUDO", str(cm.exception))


# --- TEST DE AUTENTICACIÓN JWT (Usa APITestCase) ---
class JWTAuthenticationTest(APITestCase):
    """Prueba el flujo de obtención de JWT y la validación de confirmación de email."""
    def setUp(self):
        """Configura usuarios para el flujo de obtención de token."""
        self.confirmed_admin = User.objects.create_user(
            username='admin_boss', email='boss@ok.com', password='testpassword', 
            role='ADMIN', is_email_confirmed=True
        )
        self.pending_user = User.objects.create_user(
            username='user_pending', email='pending@ok.com', password='testpassword', 
            role='USER', is_email_confirmed=False
        )
        self.login_url = reverse('token_obtain_pair')
        

    def test_login_with_username_success(self):
        """Verifica login exitoso con username y confirmación."""
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
        """Valida que el login falla (401) si el usuario no ha confirmado su email."""
        response = self.client.post(self.login_url, 
            {'username': 'pending@ok.com', 'password': 'testpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('no active account', response.data['detail'].lower())

# --- TEST DE ENDPOINTS DE USUARIO (Usa APITestCase) ---
class UserViewSetEndpointTest(APITestCase):
    """Prueba los endpoints /users/ y /users/me/ con autenticación simulada."""
    
    def setUp(self):
        """Configura todos los usuarios y URLs necesarios para las pruebas de API."""
        # Usuarios base para el ViewSet
        self.sudo_user = User.objects.create_user(username='sudo_user', email='sudo@test.com', password='test123', role='SUDO', is_email_confirmed=True)
        self.admin_user = User.objects.create_user(username='admin_user', email='admin@test.com', password='test123', role='ADMIN', is_email_confirmed=True)
        self.admin_boss = User.objects.create_user(
            username='admin_boss', email='boss@test.com', password='test123', 
            role='ADMIN', is_email_confirmed=True
        )
        self.regular_user = User.objects.create_user(username='regular_user', email='regular@test.com', password='test123', role='USER', is_email_confirmed=True)
        self.unconfirmed_user = User.objects.create_user(username='unconfirmed_user', email='unconfirmed@test.com', password='test123', role='USER', is_email_confirmed=False)
        
        # Nodos para auditoría
        Node.objects.create(title='Node 1', created_by=self.regular_user, updated_by=self.regular_user)
        Node.objects.create(title='Node 2', parent=Node.objects.get(title='Node 1'), created_by=self.regular_user, updated_by=self.regular_user)
        Node.objects.create(title='Admin Node', created_by=self.admin_user, updated_by=self.admin_user)
        
        self.users_url = reverse('user-list')
        self.me_url = reverse('user-me')
        self.change_password_url = reverse('user-change-password')
        self.token_url = reverse('token_obtain_pair')
        self.users_url = reverse('user-list')
        
        
    def _get_token(self, username):
        """Helper para obtener token JWT."""
        response = self.client.post(self.token_url, {
            'username': username,
            'password': 'test123'
        })
        return response.data['access']
    
    def _authenticate(self, user):
        """Helper para autenticar un usuario simulando el token."""
        # Ahora usamos el username/email del objeto user para obtener el token
        token = self._get_token(user.username) 
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # --- TESTS DE ENDPOINT /me/ ---
    
    def test_get_me_endpoint_success(self):
        """Verifica que un usuario autenticado puede obtener su propio perfil."""
        self._authenticate(self.regular_user)
        
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'regular_user')

    def test_get_me_endpoint_unconfirmed_user_fails(self):
        """Verifica que un usuario NO confirmado recibe 401/403 al acceder a /me."""
        # Simula que el usuario no confirmado intenta obtener un token
        token = self._get_token(self.unconfirmed_user.username) 
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(self.me_url)
        
        # El backend de autenticación falla al dar el token, resultando en 401 en el request
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    # --- TESTS DE CAMBIO DE CONTRASEÑA (REQUIERE TOKEN) ---

    def test_change_password_endpoint_success(self):
        """Verifica que un usuario puede cambiar su contraseña correctamente."""
        self._authenticate(self.regular_user)
        
        password_data = {
            'old_password': 'test123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(self.change_password_url, password_data, format='json')
        self.regular_user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.regular_user.check_password('newpassword123'))


    # --- TESTS DE PERMISOS EN LISTAR/BUSCAR USUARIOS (REQUIERE TOKEN) ---

    def test_regular_user_cannot_list_other_users(self):
        """Test que verifica que un USER no puede listar todos los usuarios."""
        self._authenticate(self.regular_user)
        response = self.client.get(self.users_url)
        
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
        self._authenticate(self.sudo_user) # <--- AHORA LLAMA AL MÉTODO LOCAL

        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        usernames = [user['username'] for user in response.data]
        self.assertIn('admin_boss', usernames) 
        self.assertIn('sudo_user', usernames)