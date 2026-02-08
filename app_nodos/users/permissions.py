# app_nodos/users/permissions.py
from rest_framework import permissions

class IsActiveAndConfirmed(permissions.BasePermission):
    """
    Permite el acceso solo a usuarios que cumplen la política mínima de seguridad:
    - Debe estar autenticado.
    - Debe estar activo (`is_active=True`).
    - Su correo debe estar confirmado (`is_email_confirmed=True`).

    Este permiso se aplica típicamente a operaciones de LECTURA (GET).
    """

    def has_permission(self, request, view):
        """
        Verifica si la solicitud cumple con los criterios de usuario activo y confirmado.
        """
        user = request.user
        
        return bool(
            request.user and 
            request.user.is_authenticated and
            request.user.is_active and
            request.user.is_email_confirmed and
            not request.user.is_deleted
        )


class IsAdminUserCustom(permissions.BasePermission):
    """
    Permite el acceso solo a roles con privilegios de escritura (ADMIN o SUDO).

    Requiere autenticación, confirmación de email, y que el rol sea 'ADMIN' o 'SUDO'.
    """

    def has_permission(self, request, view):
        """
        Verifica si el usuario tiene el rol necesario para realizar la acción
        de escritura (POST, PUT, PATCH, DELETE).
        """
        user = request.user
        
        return bool(
            request.user and 
            request.user.is_authenticated and
            request.user.role in ['ADMIN', 'SUDO']
        )


class IsSudoUser(permissions.BasePermission):
    """
    Permite el acceso exclusivo al usuario con el rol 'SUDO'.

    Este permiso se reserva para operaciones críticas del sistema.
    """

    def has_permission(self, request, view):
        """
        Verifica si el usuario autenticado posee el rol 'SUDO'.
        """
        user = request.user
        return bool(
            user and 
            user.is_authenticated and 
            user.role == 'SUDO'
        )
    
class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso que permite acceso al dueño del recurso o a ADMIN/SUDO.
    """
    message = "Solo puedes acceder a tu propia información o necesitas ser administrador."
    
    def has_object_permission(self, request, view, obj):
        # Si es el propio usuario o es ADMIN/SUDO
        return bool(
            obj == request.user or
            request.user.role in ['ADMIN', 'SUDO']
        )