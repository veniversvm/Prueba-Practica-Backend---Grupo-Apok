from rest_framework import serializers, viewsets, status
from rest_framework.response import Response
from .models import Node
from num2words import num2words
import pytz

class NodeSerializer(serializers.ModelSerializer):
    # Definimos children como un MethodField para controlar la recursividad
    children = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Node
        fields = ['id', 'title', 'parent', 'children', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_title(self, value):
        # ... (mantener lógica de conversión de números que ya teníamos)
        text_value = str(value).strip()
        if text_value.isdigit():
            lang = self.context.get('language', 'en')
            try:
                text_value = num2words(int(text_value), lang=lang)
            except NotImplementedError:
                text_value = num2words(int(text_value), lang='en')
        return text_value

    def get_children(self, obj):
        """
        Lógica de profundidad dinámica.
        """
        max_depth = self.context.get('max_depth', 0)
        current_depth = self.context.get('current_depth', 0)

        # Si aún no hemos alcanzado la profundidad máxima, serializamos los hijos
        if current_depth < max_depth:
            return NodeSerializer(
                obj.children.all(), 
                many=True, 
                context={
                    **self.context, 
                    'current_depth': current_depth + 1
                }
            ).data
        return [] # Si llegamos al límite, devolvemos lista vacía (no profundizamos más)
    
    def validate(self, data):
        """
        Validaciones de integridad de negocio.
        """
        # 1. Obtener el título ya procesado (después de validate_title)
        # Si no está en data (porque es un PATCH parcial), lo tomamos de la instancia
        title = data.get('title', getattr(self.instance, 'title', None))
        parent = data.get('parent', getattr(self.instance, 'parent', None))

        # 2. Validación de Unicidad por Nivel
        # Buscamos si existe otro nodo con el mismo título y el mismo padre
        queryset = Node.objects.filter(title=title, parent=parent)
        
        # Si estamos editando, excluimos el nodo actual de la búsqueda
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError({
                "title": f"Ya existe un nodo con el título '{title}' en este nivel de la jerarquía."
            })

        # 3. Validación de auto-referencia (ya la tenías)
        if self.instance and parent and parent.pk == self.instance.pk:
            raise serializers.ValidationError({
                "parent": "Un nodo no puede ser su propio padre."
            })

        return data
    
    def get_created_at(self, obj):
        # Obtenemos la zona horaria del contexto que pasamos desde la vista
        tz_name = self.context.get('user_timezone', 'UTC')
        try:
            user_tz = pytz.timezone(tz_name)
            # Convertimos de UTC a la zona del usuario
            local_dt = obj.created_at.astimezone(user_tz)
            return local_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
        except Exception:
            return obj.created_at.isoformat()
        
    def destroy(self, request, *args, **kwargs):
        """
        Validación Senior: Antes de borrar, verificamos si hay hijos.
        Esto evita errores 500 de integridad referencial.
        """
        instance = self.get_object()
        
        if instance.children.exists():
            return Response(
                {
                    "error": "Conflict",
                    "message": "No se puede eliminar un nodo que tiene hijos. Por favor, elimine los hijos primero."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Si no tiene hijos, procedemos con el borrado estándar
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)