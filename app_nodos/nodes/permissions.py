from rest_framework import permissions

class IsActiveAndConfirmed(permissions.BasePermission):
    """
    Permite acceso solo a usuarios activos y con email confirmado.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_active and 
            request.user.is_email_confirmed
        )

class IsAdminUserCustom(permissions.BasePermission):
    """
    Permite acceso solo a ADMIN o SUDO.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Solo ADMIN o SUDO pueden editar/borrar
        return request.user.role in ['ADMIN', 'SUDO'] and request.user.is_email_confirmed

class IsSudoUser(permissions.BasePermission):
    """
    Permite acceso exclusivo al único SUDO del sistema.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'SUDO'
        )