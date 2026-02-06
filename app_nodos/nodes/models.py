from django.db import models
from django.db.models import UniqueConstraint, Q

class Node(models.Model):
    title = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='children'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        # --- RESTRICCIÓN DE UNICIDAD SENIOR ---
        constraints = [
            # Caso 1: Unicidad cuando tiene un padre
            UniqueConstraint(
                fields=['title', 'parent'], 
                name='unique_title_per_parent',
                condition=Q(parent__isnull=False)
            ),
            # Caso 2: Unicidad para nodos raíz (donde parent es NULL)
            UniqueConstraint(
                fields=['title'], 
                name='unique_title_for_roots',
                condition=Q(parent__isnull=True)
            )
        ]

    def __str__(self):
        return self.title