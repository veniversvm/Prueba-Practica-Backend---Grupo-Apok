from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import UserManager

class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'SUDO') # Forzamos el rol SUDO para superusuarios
        extra_fields.setdefault('is_email_confirmed', True)
        return super().create_superuser(username, email, password, **extra_fields)
    
class User(AbstractUser):
    ROLE_CHOICES = (
        ('SUDO', 'Super User Ops'),
        ('ADMIN', 'Administrador'),
        ('USER', 'Usuario Regular'),
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='USER')
    is_email_confirmed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Regla de Arquitectura: Solo un SUDO permitido
        if self.role == 'SUDO':
            sudo_exists = User.objects.filter(role='SUDO').exclude(pk=self.pk).exists()
            if sudo_exists:
                raise ValidationError("Violación de Regla de Negocio: Ya existe un usuario SUDO.")
        super().save(*args, **kwargs)