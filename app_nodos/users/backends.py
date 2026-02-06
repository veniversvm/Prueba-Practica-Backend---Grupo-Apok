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

        :param request: El objeto HttpRequest.
        :param username: El valor introducido por el usuario (puede ser email o username).
        :param password: La contraseña.
        :returns: El objeto User si la autenticación es exitosa y cumple las reglas;
                  de lo contrario, retorna None.
        """
        if username is None:
            return None

        # Patrón simple de email para decidir la estrategia de búsqueda
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        is_email_format = re.match(email_pattern, username)

        try:
            if is_email_format:
                # ESTRATEGIA OPTIMIZADA: Si parece un email, busca por email o username.
                user = User.objects.get(
                    Q(email__iexact=username) | Q(username__iexact=username)
                )
            else:
                # ESTRATEGIA OPTIMIZADA: Si NO parece un email, busca SÓLO por username.
                # Esto es más rápido ya que no consulta el índice de email innecesariamente.
                user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            return None

        # 1. Validación de contraseña y estado activo (is_active)
        if user.check_password(password) and self.user_can_authenticate(user):
            
            # 2. REGLA DE NEGOCIO: El correo DEBE estar confirmado para obtener el token JWT
            if not user.is_email_confirmed:
                # Falla la autenticación por regla de seguridad.
                return None
            
            return user
        
        return None