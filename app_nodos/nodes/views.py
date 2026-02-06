from django.db.models import ProtectedError # IMPORTANTE: Faltaba este
from rest_framework import viewsets, status # IMPORTANTE: Añadir status aquí
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Node
from .serializers import NodeSerializer
import pytz

class NodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la gestión jerárquica de nodos.
    Implementa profundidad dinámica, multi-idioma y zonas horarias.
    """
    queryset = Node.objects.all()
    serializer_class = NodeSerializer

    def get_queryset(self):
        """
        Optimizamos la consulta según la acción.
        """
        queryset = Node.objects.all()
        if self.action == 'list':
            return queryset.filter(parent__isnull=True).prefetch_related('children')
        return queryset

    def get_serializer_context(self):
        """
        Enriquecemos el contexto para que el Serializer tome decisiones.
        """
        context = super().get_serializer_context()
        
        # 1. Idioma
        lang_header = self.request.headers.get('Accept-Language', 'en')
        context['language'] = lang_header.split(',')[0].split('-')[0][:2]
        
        # 2. Zona Horaria
        context['user_timezone'] = self.request.headers.get('X-Timezone', 'UTC')
        
        # 3. Profundidad (Depth)
        try:
            depth = int(self.request.query_params.get('depth', 0))
        except (ValueError, TypeError):
            depth = 0
        context['max_depth'] = depth
        context['current_depth'] = 0
        
        return context

    @extend_schema(
        parameters=[
            OpenApiParameter(name='depth', description='Nivel de profundidad', required=False, type=int),
            OpenApiParameter(name='Accept-Language', location=OpenApiParameter.HEADER, description='Idioma', type=str),
            OpenApiParameter(name='X-Timezone', location=OpenApiParameter.HEADER, description='Zona horaria', type=str),
        ]
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data) 
    
    def destroy(self, request, *args, **kwargs):
        """
        Validación Senior de borrado con manejo de excepciones.
        """
        instance = self.get_object()

        # 1. Validación Proactiva
        if instance.children.exists():
            return Response(
                {
                    "error": "Conflict",
                    "message": "No se puede eliminar un nodo que tiene hijos."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Validación Reactiva (Captura el error de integridad)
        try:
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            return Response(
                {
                    "error": "Conflict",
                    "message": "Error de integridad: Este nodo está protegido."
                },
                status=status.HTTP_400_BAD_REQUEST
            )