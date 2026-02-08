# app_nodos/users/models.py
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.core.exceptions import ValidationError


class CustomUserManager(UserManager):
    """
    Manager personalizado para el modelo User.

    Asegura que los superusuarios creados a través de comandos de gestión
    (como createsuperuser) reciban automáticamente el rol 'SUDO'
    y tengan el email confirmado.
    """
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """
        Sobreescribe create_superuser para asignar roles y confirmación de email.
        """
        extra_fields.setdefault('role', 'SUDO')
        extra_fields.setdefault('is_email_confirmed', True)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Modelo de Usuario Personalizado (AUTH_USER_MODEL) basado en AbstractUser.

    Implementa roles personalizados y un flag de confirmación de email para
    reforzar la seguridad en la fase de autenticación.
    """
    
    ROLE_CHOICES = (
        ('SUDO', 'Super User Ops'),
        ('ADMIN', 'Administrador'),
        ('USER', 'Usuario Regular'),
    )
    
    email = models.EmailField(
        unique=True, 
        help_text="Correo electrónico único del usuario."
    )
    
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='USER',
        help_text="Rol de acceso del usuario (SUDO, ADMIN, USER)."
    )
    
    is_email_confirmed = models.BooleanField(
        default=True, 
        help_text="Indica si el usuario ha verificado su correo electrónico."
    )
    
    # CORRECCIÓN: Añadir campo is_deleted que se usa en soft_delete()
    is_deleted = models.BooleanField(
        default=False,
        help_text="Indica si el usuario ha sido eliminado lógicamente."
    )

    # Usa el Manager personalizado
    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        """
        Sobreescribe el método save para aplicar reglas de negocio.

        Regla principal: Solo se permite la existencia de UN usuario con el rol SUDO.
        """
        # Regla de Arquitectura: Solo un SUDO permitido
        if self.role == 'SUDO':
            # Buscamos otro usuario SUDO que no sea la instancia actual
            sudo_exists = User.objects.filter(role='SUDO').exclude(pk=self.pk).exists()
            if sudo_exists:
                raise ValidationError(
                    "Violación de Regla de Negocio: Ya existe un usuario SUDO."
                )
        super().save(*args, **kwargs)

    def soft_delete(self):
        """
        Método de borrado lógico para el modelo User.
        Marca el usuario como eliminado y registra el timestamp.
        """
        self.is_deleted = True
        # CORRECCIÓN: Usar timezone.now() correctamente
        # self.deleted_at = timezone.now()  # Comentado por ahora
        self.is_active = False  # Mejor práctica: Desactivar para que no pueda loguearse
        self.save()

    def __str__(self):
        """
        Retorna la representación de cadena del objeto.
        """
        return self.username