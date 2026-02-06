from django.db import models
from django.db.models import UniqueConstraint, Q
from django.conf import settings
from django.utils import timezone # Usar la utilidad de Django

class Node(models.Model):
    title = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='children'
    )
    
    # --- Auditoría ---
    # Nota: on_delete=models.SET_NULL asegura que si el usuario se borra, 
    # el nodo permanezca pero el campo quede vacío.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='nodes_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='nodes_updated'
    )

    # --- Soft Delete ---
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            # Caso 1: Unicidad cuando tiene un padre (Solo para nodos ACTIVOS)
            UniqueConstraint(
                fields=['title', 'parent'], 
                name='unique_title_per_parent',
                condition=Q(is_deleted=False, parent__isnull=False)
            ),
            # Caso 2: Unicidad para nodos raíz (Solo para nodos ACTIVOS)
            UniqueConstraint(
                fields=['title'], 
                name='unique_title_for_roots',
                condition=Q(is_deleted=False, parent__isnull=True)
            )
        ]

    def soft_delete(self):
        """Método personalizado para borrado lógico"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return self.title