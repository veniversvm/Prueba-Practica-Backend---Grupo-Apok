from django.db import models
from django.db.models import UniqueConstraint, Q
from django.conf import settings
from django.utils import timezone

class Node(models.Model):
    """
    Modelo base para representar un nodo en una estructura jerárquica de árbol.

    Implementa:
    - Autorreferencia (parent/children) para la jerarquía.
    - Soft Delete (Borrado Lógico) para preservar la integridad de los datos.
    - Auditoría para rastrear quién creó y modificó el nodo.
    - Restricciones de unicidad por nivel jerárquico.
    """

    title = models.CharField(
        max_length=255, 
        help_text="Título del nodo. Puede ser la representación textual de un número."
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='children',
        help_text="Nodo padre. Null si es un nodo raíz."
    )
    
    # --- Auditoría ---
    created_at = models.DateTimeField(
        auto_now_add=True, 
        help_text="Fecha y hora de creación (UTC)."
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        help_text="Última fecha y hora de modificación (UTC)."
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='nodes_created',
        help_text="Usuario que creó el nodo."
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='nodes_updated',
        help_text="Último usuario que modificó el nodo."
    )

    # --- Soft Delete ---
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
        """Configuraciones del modelo, incluyendo ordenamiento y restricciones."""

        ordering = ['-created_at']
        verbose_name = "Nodo"
        verbose_name_plural = "Nodos"
        constraints = [
            # Restricción 1: Unicidad del título dentro del mismo padre (solo nodos activos).
            UniqueConstraint(
                fields=['title', 'parent'], 
                name='unique_title_per_parent',
                condition=Q(is_deleted=False, parent__isnull=False)
            ),
            # Restricción 2: Unicidad del título para todos los nodos raíz (solo nodos activos).
            UniqueConstraint(
                fields=['title'], 
                name='unique_title_for_roots',
                condition=Q(is_deleted=False, parent__isnull=True)
            )
        ]

    def soft_delete(self):
        """
        Realiza un borrado lógico del nodo.

        Establece 'is_deleted' a True y registra el tiempo actual.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        """
        Retorna la representación de cadena del objeto.
        """
        return self.title