# app_nodos/nodes/admin.py
from django.contrib import admin
from .models import Node

@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Node.
    """
    
    # Campos a mostrar en la lista
    list_display = [
        'id',           # Mostrar ID
        'content',      # Mostrar contenido (lo que antes era title)
        'parent',       # Mostrar padre
        'created_at',   # Mostrar fecha de creación
        'is_deleted',   # Mostrar estado de borrado
    ]
    
    # Campos de solo lectura
    readonly_fields = [
        'id',           # ID es auto-generado
        'created_at',   # Fecha de creación no se edita
        'updated_at',   # Fecha de actualización no se edita
        'deleted_at',   # Fecha de borrado no se edita directamente
    ]
    
    # Campos para búsqueda
    search_fields = [
        'content',      # Buscar por contenido
        'id',           # Buscar por ID
    ]
    
    # Filtros
    list_filter = [
        'is_deleted',   # Filtrar por estado de borrado
        'created_at',   # Filtrar por fecha
        'parent',       # Filtrar por padre
    ]
    
    # Ordenamiento por defecto
    ordering = ['-created_at']  # Solo por created_at, ya no por title
    
    # Jerarquía por padre
    hierarchy = 'parent'
    
    # Campos a mostrar en el formulario de edición
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'content', 'parent')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('is_deleted',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """
        Personalizar el queryset para el admin.
        Por defecto mostrar todos, incluidos borrados lógicos.
        """
        return Node.objects.all()
    
    def has_delete_permission(self, request, obj=None):
        """
        Controlar permisos de borrado.
        Por defecto permitir borrado físico solo para superusuarios.
        """
        if obj and obj.children.exists():
            return False  # No permitir borrar si tiene hijos
        return super().has_delete_permission(request, obj)
    
    def delete_model(self, request, obj):
        """
        Sobreescribir borrado para usar soft delete.
        """
        obj.soft_delete()
        self.message_user(request, f"Nodo '{obj.content}' marcado como borrado lógico.")
    
    def delete_queryset(self, request, queryset):
        """
        Sobreescribir borrado masivo.
        """
        for obj in queryset:
            obj.soft_delete()
        self.message_user(request, f"{queryset.count()} nodos marcados como borrados lógicos.")