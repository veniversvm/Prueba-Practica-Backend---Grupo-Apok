from django.db import models
from django.db.models import UniqueConstraint, Q
from django.utils import timezone


class Node(models.Model):
    """
    Modelo para representar un nodo en una estructura jerárquica de árbol.
    """
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='children',
        help_text="Nodo padre. Null si es un nodo raíz."
    )
    
    content = models.CharField(
        max_length=255,
        help_text="Contenido o descripción del nodo."
    )
    
    # NOTA: Eliminamos el campo 'title' del modelo
    # El título se generará dinámicamente en el serializador
    
    created_at = models.DateTimeField(
        auto_now_add=True, 
        help_text="Fecha y hora de creación (UTC)."
    )
    
    # --- Campos opcionales ---
    updated_at = models.DateTimeField(
        auto_now=True, 
        help_text="Última fecha y hora de modificación (UTC)."
    )
    
    is_deleted = models.BooleanField(
        default=False, 
        help_text="Indica si el nodo ha sido borrado lógicamente."
    )
    
    deleted_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha y hora del borrado lógico."
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Nodo"
        verbose_name_plural = "Nodos"
        constraints = [
            UniqueConstraint(
                fields=['content', 'parent'], 
                name='unique_content_per_parent',
                condition=Q(is_deleted=False, parent__isnull=False)
            ),
            UniqueConstraint(
                fields=['content'], 
                name='unique_content_for_roots',
                condition=Q(is_deleted=False, parent__isnull=True)
            )
        ]

    def soft_delete(self):
        """
        Realiza un borrado lógico del nodo.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.id}: {self.content}"