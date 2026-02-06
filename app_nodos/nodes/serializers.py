from rest_framework import serializers
from .models import Node
from num2words import num2words
import pytz

class NodeSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Node.

    Gestiona la transformación del 'title' (número a palabra) y
    la representación jerárquica con profundidad dinámica.
    También implementa la lógica de auditoría y localización de fechas.
    """
    
    children = serializers.SerializerMethodField(
        help_text="Lista de nodos hijos (recursividad limitada por depth)."
    )
    created_at = serializers.SerializerMethodField(
        help_text="Fecha de creación ajustada a la zona horaria del cliente."
    )
    # Campos de Auditoría (Solo lectura)
    created_by_name = serializers.ReadOnlyField(
        source='created_by.username', 
        help_text="Nombre del usuario que creó el nodo."
    )
    updated_by_name = serializers.ReadOnlyField(
        source='updated_by.username', 
        help_text="Nombre del usuario que modificó por última vez el nodo."
    )

    class Meta:
        """Configuración de metadatos del Serializer."""
        model = Node
        fields = [
            'id', 'title', 'parent', 'children', 
            'created_at', 'created_by_name', 'updated_by_name'
        ]
        read_only_fields = [
            'id', 'created_at', 'created_by_name', 'updated_by_name'
        ]

    def validate_title(self, value):
        """
        Saneamiento y conversión de números a palabras.

        El 'title' es transformado de número a su representación textual
        basado en el header 'Accept-Language' del contexto.

        :param value: El título enviado en el request.
        :returns: El título saneado y/o convertido.
        """
        text_value = str(value).strip()
        if text_value.isdigit():
            lang = self.context.get('language', 'en')
            try:
                text_value = num2words(int(text_value), lang=lang)
            except NotImplementedError:
                # Fallback a inglés si el idioma no es soportado
                text_value = num2words(int(text_value), lang='en')
        return text_value

    def get_children(self, obj):
        """
        Implementa la lógica de serialización recursiva y profundidad.

        Filtra los hijos por `is_deleted=False` para preservar la integridad de la vista.

        :param obj: Instancia del nodo actual.
        :returns: Lista de hijos serializados o lista vacía si se alcanza `max_depth`.
        """
        max_depth = self.context.get('max_depth', 0)
        current_depth = self.context.get('current_depth', 0)

        if current_depth < max_depth:
            # Filtramos solo por nodos activos
            active_children = obj.children.filter(is_deleted=False)
            return NodeSerializer(
                active_children, 
                many=True, 
                context={
                    **self.context, 
                    'current_depth': current_depth + 1
                }
            ).data
        return []

    def validate(self, data):
        """
        Validaciones de integridad de negocio.

        Incluye la validación de unicidad por nivel y la prevención de auto-referencia.

        :param data: Diccionario de datos validados.
        :raises serializers.ValidationError: Si se viola la unicidad o auto-referencia.
        :returns: Diccionario de datos para guardar.
        """
        title = data.get('title', getattr(self.instance, 'title', None))
        parent = data.get('parent', getattr(self.instance, 'parent', None))

        # 1. Validación de Unicidad por Nivel (Solo contra nodos ACTIVOS)
        queryset = Node.objects.filter(
            title__iexact=title, 
            parent=parent, 
            is_deleted=False
        )
        
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError({
                "title": f"Ya existe un nodo activo con el título '{title}' en este nivel."
            })

        # 2. Validación de auto-referencia (Un nodo no puede ser su propio padre)
        if self.instance and parent and parent.pk == self.instance.pk:
            raise serializers.ValidationError({
                "parent": "Un nodo no puede ser su propio padre."
            })

        return data

    def get_created_at(self, obj):
        """
        Convierte la fecha de creación (UTC) a la zona horaria solicitada por el cliente.

        :param obj: Instancia del nodo.
        :returns: La fecha formateada en la zona horaria del cliente.
        """
        tz_name = self.context.get('user_timezone', 'UTC')
        try:
            user_tz = pytz.timezone(tz_name)
            local_dt = obj.created_at.astimezone(user_tz)
            return local_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
        except Exception:
            # Fallback seguro a ISO si la zona horaria no es válida
            return obj.created_at.isoformat()