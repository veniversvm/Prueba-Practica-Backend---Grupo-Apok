# app_nodos/nodes/permissions.py
from rest_framework import permissions

class IsActiveAndConfirmed(permissions.BasePermission):
    """
    Permite el acceso a usuarios que cumplen la política de seguridad mínima:
    - Autenticado.
    - Usuario activo (`is_active=True`).
    - Correo electrónico confirmado (`is_email_confirmed=True`).

    Este permiso se usa típicamente para las operaciones de LECTURA (GET/LIST).
    """

    def has_permission(self, request, view):
        """
        Retorna True si el usuario cumple la política.
        """
        # Se asume que request.user existe si el AuthenticationBackend (JWT) pasó.
        user = request.user
        
        return bool(
            user and 
            user.is_authenticated and 
            user.is_active and 
            user.is_email_confirmed
        )


class IsAdminUserCustom(permissions.BasePermission):
    """
    Permite acceso de ESCRITURA (POST, PUT, DELETE) solo a roles ADMIN o SUDO.

    Requiere que el usuario esté autenticado y tenga el email confirmado.
    """

    def has_permission(self, request, view):
        """
        Retorna True si el usuario tiene el rol y el email confirmado.
        """
        user = request.user
        
        # Primero, verifica la autenticación.
        if not (user and user.is_authenticated):
            return False
        
        # Regla de Negocio: Solo ADMIN o SUDO pueden editar/borrar/crear.
        # Y su correo debe estar confirmado.
        is_allowed_role = user.role in ['ADMIN', 'SUDO']
        
        return bool(is_allowed_role and user.is_email_confirmed)


class IsSudoUser(permissions.BasePermission):
    """
    Permite acceso exclusivo al rol SUDO.

    Este permiso se usa para endpoints críticos de gestión del sistema.
    """

    def has_permission(self, request, view):
        """
        Retorna True si el usuario es SUDO y está autenticado.
        """
        user = request.user
        
        return bool(
            user and 
            user.is_authenticated and 
            user.role == 'SUDO'
        )