# users/admin.py (modificado)
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()

# Solo registrar si no está ya registrado
try:
    @admin.register(User)
    class CustomUserAdmin(BaseUserAdmin):
        """
        Admin personalizado para el modelo User personalizado.
        """
        list_display = ('username', 'email', 'role', 'is_email_confirmed', 'is_active')
        list_filter = ('role', 'is_email_confirmed', 'is_active', 'is_staff')
        fieldsets = (
            (None, {'fields': ('username', 'password')}),
            ('Información Personal', {'fields': ('first_name', 'last_name', 'email')}),
            ('Roles y Permisos', {'fields': ('role', 'is_email_confirmed', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
            ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
        )
        add_fieldsets = (
            (None, {
                'classes': ('wide',),
                'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_email_confirmed'),
            }),
        )
        search_fields = ('username', 'email', 'first_name', 'last_name')
        ordering = ('-date_joined',)
except admin.sites.AlreadyRegistered:
    # El modelo ya está registrado, no hacer nada
    pass