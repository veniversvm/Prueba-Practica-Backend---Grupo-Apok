from django.db.models import ProtectedError # IMPORTANTE: Faltaba este
from rest_framework import viewsets, status # IMPORTANTE: Añadir status aquí
from rest_framework.response import Response
from nodes.permissions import IsActiveAndConfirmed, IsAdminUserCustom
from .models import Node
from .serializers import NodeSerializer
from django.utils import timezone

class NodeViewSet(viewsets.ModelViewSet):
    serializer_class = NodeSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUserCustom()]
        return [IsActiveAndConfirmed()]

    def get_queryset(self):
        # Regla Senior: La API nunca muestra nodos borrados lógicamente
        queryset = Node.objects.filter(is_deleted=False)
        if self.action == 'list':
            return queryset.filter(parent__isnull=True).prefetch_related('children')
        return queryset

    def perform_create(self, serializer):
        # Guardamos quién crea el nodo
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        # Guardamos quién actualiza el nodo
        serializer.save(updated_by=self.request.user)


    def destroy(self, request, *args, **kwargs):
        """Implementación Senior de Borrado Lógico."""
        instance = self.get_object()
        
        # Validar si tiene hijos activos (no borrados)
        if instance.children.filter(is_deleted=False).exists():
            return Response(
                {"error": "No se puede eliminar un nodo que tiene hijos activos."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Llamamos al método soft_delete que creamos en el modelo
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)