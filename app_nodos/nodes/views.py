from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status, viewsets
from rest_framework.response import Response

from nodes.permissions import IsActiveAndConfirmed, IsAdminUserCustom
from .models import Node
from .serializers import NodeSerializer


CACHE_TIMEOUT = 180
CACHE_VERSION_KEY = "node_list_cache_version"


class NodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la gestión jerárquica de nodos.

    Características:
    - Soft delete
    - Permisos personalizados
    - Cache del listado con invalidación por versión
    """

    serializer_class = NodeSerializer

    def _get_cache_version(self):
        """
        Obtiene la versión actual del caché para el listado de nodos.
        """
        return cache.get(CACHE_VERSION_KEY, 1)

    def _invalidate_list_cache(self):
        """
        Invalida el caché del listado incrementando la versión.
        """
        version = self._get_cache_version()
        cache.set(CACHE_VERSION_KEY, version + 1)

    @method_decorator(
        lambda func: cache_page(
            CACHE_TIMEOUT,
            key_prefix=lambda request: f"node_list_v{cache.get(CACHE_VERSION_KEY, 1)}",
        )(func)
    )
    def list(self, request, *args, **kwargs):
        """
        Lista los nodos raíz.
        El resultado es cacheado por 180 segundos y versionado.
        """
        return super().list(request, *args, **kwargs)

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUserCustom()]
        return [IsActiveAndConfirmed()]

    def get_queryset(self):
        queryset = Node.objects.filter(is_deleted=False)

        if self.action == "list":
            return queryset.filter(
                parent__isnull=True
            ).prefetch_related("children")

        return queryset

    def perform_create(self, serializer):
        self._invalidate_list_cache()
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        self._invalidate_list_cache()
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        Borrado lógico de un nodo hoja.
        """
        instance = self.get_object()

        if instance.children.filter(is_deleted=False).exists():
            return Response(
                {"error": "No se puede eliminar un nodo que tiene hijos activos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self._invalidate_list_cache()
        instance.soft_delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
