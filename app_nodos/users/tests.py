from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class UserSecurityTest(TestCase):
    def setUp(self):
        # Creamos dos usuarios base
        self.confirmed_admin = User.objects.create_user(
            username='admin_ok', email='admin@ok.com', password='testpassword', 
            role='ADMIN', is_email_confirmed=True
        )
        self.pending_user = User.objects.create_user(
            username='user_no_email', email='user@no.com', password='testpassword', 
            role='USER', is_email_confirmed=False
        )

    def test_sudo_unique_constraint(self):
        """Verificar que solo se puede crear un usuario con rol SUDO en el sistema."""
        User.objects.create_user(
            username='sudo_1', email='sudo1@sys.com', password='testpassword', 
            role='SUDO', is_email_confirmed=True
        )
        # Intentar crear un segundo SUDO debe lanzar la excepción
        with self.assertRaises(ValidationError) as cm:
            User.objects.create_user(
                username='sudo_2', email='sudo2@sys.com', password='testpassword', 
                role='SUDO', is_email_confirmed=True
            )
        # Verificamos que el mensaje CONCUERDE EXACTAMENTE con lo que lanza el modelo
        self.assertIn("Ya existe un usuario SUDO", str(cm.exception)) # <--- LÍNEA CORREGIDA

class JWTAuthenticationTest(APITestCase):
    def setUp(self):
        # Usuarios para probar el backend de autenticación
        self.confirmed_admin = User.objects.create_user(
            username='admin_boss', email='boss@ok.com', password='testpassword', 
            role='ADMIN', is_email_confirmed=True
        )
        self.pending_user = User.objects.create_user(
            username='user_pending', email='pending@ok.com', password='testpassword', 
            role='USER', is_email_confirmed=False
        )
        self.login_url = reverse('token_obtain_pair')

    # --- TESTS DE LOGIN DUAL Y CONFIRMACIÓN ---

    def test_login_with_username_success(self):
        """Login con username y email confirmado debe retornar 200"""
        response = self.client.post(self.login_url, 
            {'username': 'admin_boss', 'password': 'testpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_login_with_email_success(self):
        """Login con email y email confirmado debe retornar 200"""
        response = self.client.post(self.login_url, 
            {'username': 'boss@ok.com', 'password': 'testpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_login_with_unconfirmed_email_fails(self):
        """Login con usuario NO confirmado debe retornar 401"""
        # El backend de autenticación debe fallar (retorna None), lo que resulta en 401
        response = self.client.post(self.login_url, 
            {'username': 'pending@ok.com', 'password': 'testpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('no active account', response.data['detail'].lower())