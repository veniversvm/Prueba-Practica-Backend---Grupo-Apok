# app_nodos/users/backends.py
import re
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """
    Backend de autenticación avanzado para el sistema.

    Permite el inicio de sesión utilizando el correo electrónico o el nombre
    de usuario (login dual). Implementa optimización de búsqueda y una
    regla de negocio de seguridad.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Intenta autenticar al usuario basado en las credenciales proporcionadas.

        Args:
            request: El objeto HttpRequest.
            username: El valor introducido por el usuario (puede ser email o username).
            password: La contraseña.
            
        Returns:
            User: El objeto User si la autenticación es exitosa y cumple las reglas,
                  de lo contrario, retorna None.
        """
        # CORRECCIÓN: También verificar si username viene vacío
        if not username or password is None:
            return None

        # Normalizar el username (trim y lowercase para emails)
        username = username.strip()
        
        # Patrón mejorado de email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_email_format = re.match(email_pattern, username)
        
        # CORRECCIÓN: También aceptar username en el parámetro email
        # (algunos formularios Django pueden enviar 'email' en lugar de 'username')
        if not is_email_format and 'email' in kwargs:
            email = kwargs.get('email', '').strip()
            if email:
                is_email_format = re.match(email_pattern, email)
                if is_email_format:
                    username = email

        try:
            if is_email_format:
                # MEJORA: Buscar primero por email (más común cuando es email)
                # y usar select_related/prefetch_related si hay relaciones
                user = User.objects.filter(
                    Q(email__iexact=username) | Q(username__iexact=username)
                ).first()  # Usar first() en lugar de get() para mejor manejo
            else:
                # Buscar solo por username
                user = User.objects.filter(username__iexact=username).first()
                
            # CORRECCIÓN: Si no encontramos usuario
            if not user:
                return None
                
        except User.DoesNotExist:
            return None
        except Exception as e:
            # MEJORA: Log de errores inesperados (opcional)
            # import logging
            # logger = logging.getLogger(__name__)
            # logger.error(f"Error en autenticación: {e}")
            return None

        # 1. Validación de contraseña y estado activo (is_active)
        # MEJORA: Verificar password primero (más rápido)
        if not user.check_password(password):
            return None
            
        # 2. Verificar que el usuario pueda autenticarse (is_active, etc.)
        if not self.user_can_authenticate(user):
            return None
            
        # 3. REGLA DE NEGOCIO: El correo DEBE estar confirmado para obtener el token JWT
        # CORRECCIÓN: También verificar que no esté eliminado lógicamente
        if not user.is_email_confirmed or user.is_deleted:
            # Falla la autenticación por regla de seguridad.
            return None
        
        return user
    
    def get_user(self, user_id):
        """
        Obtiene un usuario por su ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            User: El objeto User si existe y está activo, de lo contrario None.
        """
        try:
            user = User.objects.get(pk=user_id)
            # MEJORA: Verificar también is_email_confirmed y is_deleted
            if (user.is_active and 
                user.is_email_confirmed and 
                not user.is_deleted):
                return user
            return None
        except User.DoesNotExist:
            return None