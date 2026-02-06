from django.contrib import admin
from .models import Node

# Opcional: Para una mejor interfaz de árbol, necesitarías una librería como 
# django-mptt o django-treebeard. Pero para esta prueba, usaremos la vista simple 
# con filtrado.

@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    """
    Configuración de la interfaz de administración para el modelo Node.
    """
    list_display = (
        'title', 
        'parent', 
        'is_deleted', 
        'created_at', 
        'created_by', 
        'updated_by'
    )
    
    # Permite filtrar por nodo padre para ver la jerarquía por nivel
    list_filter = (
        'parent', 
        'is_deleted',
    )
    
    # Búsqueda por título e ID
    search_fields = (
        'title', 
        'id'
    )

    # Ordenar por defecto para ver los nodos raíz primero
    ordering = ('parent__isnull', 'title') 

    # Campos de auditoría como solo lectura
    readonly_fields = (
        'created_at', 
        'updated_at', 
        'created_by', 
        'updated_by', 
        'deleted_at'
    )

    fieldsets = (
        (None, {
            'fields': ('title', 'parent')
        }),
        ('Auditoría y Estado', {
            'fields': (
                'is_deleted', 'deleted_at', 
                'created_at', 'updated_at', 
                'created_by', 'updated_by'
            ),
            'classes': ('collapse',) # Oculta la auditoría para una vista más limpia
        }),
    )

# --- FIN DE NODES/ADMIN.PY ---

# También registramos el modelo de usuario custom en users/admin.py:
# (Asumiendo que creaste users/admin.py)

from django.contrib.auth.admin import UserAdmin
from users.models import User

# Desregistrar el UserAdmin por defecto (si ya estuviera registrado)
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Configuración de la interfaz de administración para el modelo User customizado.
    """
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'is_email_confirmed')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'is_email_confirmed')}),
    )
    list_display = ('username', 'email', 'role', 'is_email_confirmed', 'is_staff')
    list_filter = ('role', 'is_email_confirmed', 'is_staff', 'is_active')