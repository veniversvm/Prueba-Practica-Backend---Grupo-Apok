import re
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """
    Backend de autenticación inteligente:
    1. Detecta si el input es un patrón de email.
    2. Busca por Email/Username o solo Username según corresponda.
    3. Valida que el email esté confirmado.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None

        # Patrón simple de email para decidir la estrategia de búsqueda
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        is_email_format = re.match(email_pattern, username)

        try:
            if is_email_format:
                # Estrategia A: El input parece un email. 
                # Buscamos en ambos campos por si un username tiene formato de email (edge case)
                user = User.objects.get(Q(email__iexact=username) | Q(username__iexact=username))
            else:
                # Estrategia B: El input NO es un email. 
                # Buscamos solo por username (Optimización de índice)
                user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            return None

        # Validación de contraseña y estado activo (is_active)
        if user.check_password(password) and self.user_can_authenticate(user):
            # REGLA DE NEGOCIO: El correo DEBE estar confirmado
            if not user.is_email_confirmed:
                # Podríamos loguear este intento fallido para auditoría
                return None
            return user
        
        return None