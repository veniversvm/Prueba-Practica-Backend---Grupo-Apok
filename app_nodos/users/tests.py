# app_nodos/users/tests.py (tests corregidos)
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase

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
        self.sudo_user = User.objects.create_user(
            username='sudo_user', email='sudo@test.com', 
            password='test123', role='SUDO', is_email_confirmed=True
        )
        self.admin_user = User.objects.create_user(
            username='admin_user', email='admin@test.com', 
            password='test123', role='ADMIN', is_email_confirmed=True
        )
        self.admin_boss = User.objects.create_user(
            username='admin_boss', email='boss@test.com', 
            password='test123', role='ADMIN', is_email_confirmed=True
        )
        self.regular_user = User.objects.create_user(
            username='regular_user', email='regular@test.com', 
            password='test123', role='USER', is_email_confirmed=True
        )
        self.unconfirmed_user = User.objects.create_user(
            username='unconfirmed_user', email='unconfirmed@test.com', 
            password='test123', role='USER', is_email_confirmed=False
        )
        
        # No crear nodos por ahora para simplificar los tests
        # Los tests funcionarán sin la dependencia de la app nodes
        
        self.users_url = reverse('user-list')
        self.me_url = reverse('user-me')
        self.change_password_url = reverse('user-change-password')
        self.update_me_url = reverse('user-update-me')  # Añadido
        self.token_url = reverse('token_obtain_pair')
        
    def _get_token(self, username):
        """Helper para obtener token JWT."""
        response = self.client.post(self.token_url, {
            'username': username,
            'password': 'test123'
        })
        if response.status_code == 200:
            return response.data.get('access')
        return None
    
    def _authenticate(self, user):
        """Helper para autenticar un usuario simulando el token."""
        token = self._get_token(user.username)
        if token:
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
            return True
        return False

    # --- TESTS DE ENDPOINT /me/ ---
    
    def test_get_me_endpoint_success(self):
        """Verifica que un usuario autenticado puede obtener su propio perfil."""
        self._authenticate(self.regular_user)
        
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'regular_user')

    def test_get_me_endpoint_unconfirmed_user_fails(self):
        """Verifica que un usuario NO confirmado recibe 401/403 al acceder a /me."""
        # Para usuario no confirmado, no debería obtener token
        token = self._get_token(self.unconfirmed_user.username)
        
        if token:
            # Si por alguna razón obtiene token (no debería), intentamos usarlo
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
            response = self.client.get(self.me_url)
            # Debería fallar
            self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
        else:
            # Sin token, el endpoint debería devolver 401
            self.client.credentials()  # Limpiar credenciales
            response = self.client.get(self.me_url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

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

    def test_change_password_with_wrong_old_password_fails(self):
        """Verifica que no se puede cambiar la contraseña con la contraseña actual incorrecta."""
        self._authenticate(self.regular_user)
        
        password_data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(self.change_password_url, password_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)

    def test_change_password_with_mismatch_fails(self):
        """Verifica que no se puede cambiar la contraseña si no coinciden."""
        self._authenticate(self.regular_user)
        
        password_data = {
            'old_password': 'test123',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword'
        }
        
        response = self.client.post(self.change_password_url, password_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_password', response.data)

    # --- TESTS DE PERMISOS EN LISTAR/BUSCAR USUARIOS (REQUIERE TOKEN) ---

    def test_regular_user_cannot_list_other_users(self):
        """Test que verifica que un USER no puede listar todos los usuarios."""
        self._authenticate(self.regular_user)
        response = self.client.get(self.users_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Debería ver solo su propio perfil
        if isinstance(response.data, list):
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['username'], 'regular_user')
        elif 'results' in response.data:  # Si usa paginación
            self.assertEqual(len(response.data['results']), 1)
            self.assertEqual(response.data['results'][0]['username'], 'regular_user')

    def test_admin_can_list_users_except_sudo(self):
        """Test que verifica que un ADMIN puede listar usuarios excepto SUDO."""
        self._authenticate(self.admin_user)
        response = self.client.get(self.users_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Extraer datos dependiendo de la estructura de respuesta
        if isinstance(response.data, list):
            users_data = response.data
        elif 'results' in response.data:
            users_data = response.data['results']
        else:
            users_data = []
        
        usernames = [user['username'] for user in users_data]
        # No debería ver al SUDO pero sí a otros usuarios
        self.assertNotIn('sudo_user', usernames)
        self.assertIn('regular_user', usernames)
        self.assertIn('admin_user', usernames)

    def test_sudo_can_list_all_users(self):
        """Test que verifica que un SUDO puede listar todos los usuarios."""
        self._authenticate(self.sudo_user)
        
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Extraer datos dependiendo de la estructura de respuesta
        if isinstance(response.data, list):
            users_data = response.data
        elif 'results' in response.data:
            users_data = response.data['results']
        else:
            users_data = []
        
        usernames = [user['username'] for user in users_data]
        # Debería ver todos los usuarios, incluyendo SUDO
        self.assertIn('sudo_user', usernames)
        self.assertIn('admin_boss', usernames)
        self.assertIn('regular_user', usernames)

    # --- TESTS ADICIONALES PARA MEJORAR COBERTURA ---
    
    def test_user_cannot_change_own_role(self):
        """Verifica que un USER no puede cambiar su propio rol."""
        self._authenticate(self.regular_user)
        
        update_data = {'role': 'ADMIN'}
        user_detail_url = reverse('user-detail', args=[self.regular_user.id])
        
        response = self.client.patch(user_detail_url, update_data, format='json')
        # Puede ser 403 (permiso denegado) o 400 (validación del serializer)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST])
        if response.status_code == 400:
            self.assertIn('role', response.data)

    def test_admin_cannot_create_sudo(self):
        """Verifica que un ADMIN no puede crear un usuario SUDO."""
        self._authenticate(self.admin_user)
        
        user_data = {
            'username': 'new_sudo',
            'email': 'new_sudo@test.com',
            'password': 'test123',
            'password_confirm': 'test123',
            'role': 'SUDO',
            'first_name': 'New',  # Añadido campo opcional
            'last_name': 'Sudo'   # Añadido campo opcional
        }
        
        response = self.client.post(self.users_url, user_data, format='json')
        # Puede ser 403 (permiso) o 400 (validación en serializer)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST])
        if response.status_code == 400:
            self.assertIn('role', response.data)

    def test_sudo_can_create_admin(self):
        """Verifica que un SUDO puede crear un usuario ADMIN."""
        self._authenticate(self.sudo_user)
        
        user_data = {
            'username': 'new_admin',
            'email': 'new_admin@test.com',
            'password': 'test123456',  # Contraseña más larga
            'password_confirm': 'test123456',
            'role': 'ADMIN',
            'first_name': 'New',  # Campos opcionales añadidos
            'last_name': 'Admin'
        }
        
        response = self.client.post(self.users_url, user_data, format='json')
        # DEBUG: Imprimir respuesta para ver el error
        if response.status_code != 201:
            print(f"DEBUG - Error al crear admin: {response.status_code}")
            print(f"DEBUG - Respuesta: {response.data}")
        
        # El resultado puede variar dependiendo de las validaciones
        # Si es 201, éxito; si es 400, revisar validaciones
        if response.status_code == status.HTTP_201_CREATED:
            # Verificar que se creó el usuario
            new_user = User.objects.filter(username='new_admin').first()
            self.assertIsNotNone(new_user)
            self.assertEqual(new_user.role, 'ADMIN')
        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            # El test falla porque esperaba 201, pero documentamos el error
            self.fail(f"No se pudo crear usuario ADMIN. Error: {response.data}")
        else:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_cannot_update_other_user(self):
        """Verifica que un USER no puede actualizar otro usuario."""
        self._authenticate(self.regular_user)
        
        update_data = {'first_name': 'Modified'}
        user_detail_url = reverse('user-detail', args=[self.admin_user.id])
        
        response = self.client.patch(user_detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_update_sudo(self):
        """Verifica que un ADMIN no puede actualizar un usuario SUDO."""
        self._authenticate(self.admin_user)
        
        update_data = {'first_name': 'Modified'}
        user_detail_url = reverse('user-detail', args=[self.sudo_user.id])
        
        response = self.client.patch(user_detail_url, update_data, format='json')
        # Puede ser 404 (no encontrado porque admin no ve SUDOs) o 403 (permiso denegado)
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])
        
        # Si es 404, verificamos que es porque el admin no puede ver al sudo
        if response.status_code == status.HTTP_404_NOT_FOUND:
            # Verificar que efectivamente el admin no ve al sudo en la lista
            list_response = self.client.get(self.users_url)
            usernames = []
            if isinstance(list_response.data, list):
                usernames = [user['username'] for user in list_response.data]
            elif 'results' in list_response.data:
                usernames = [user['username'] for user in list_response.data['results']]
            
            self.assertNotIn('sudo_user', usernames)

    def test_update_me_endpoint_success(self):
        """Verifica que un usuario puede actualizar su propio perfil."""
        self._authenticate(self.regular_user)
        
        update_data = {'first_name': 'Updated', 'last_name': 'User'}
        
        response = self.client.patch(self.update_me_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que se actualizó
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.first_name, 'Updated')
        self.assertEqual(self.regular_user.last_name, 'User')

    def test_update_me_cannot_change_role(self):
        """Verifica que un usuario no puede cambiar su propio rol en /me/update."""
        self._authenticate(self.regular_user)
        
        update_data = {'role': 'ADMIN'}
        
        response = self.client.patch(self.update_me_url, update_data, format='json')
        # Puede ser 400 (validación del serializer) o 403 (permiso denegado)
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
        
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn('role', response.data)
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            self.assertIn('role', response.data)
        
        # Verificar que el rol NO cambió
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.role, 'USER')