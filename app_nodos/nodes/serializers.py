from rest_framework import serializers
from .models import Node
from num2words import num2words
import pytz

class NodeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    # Añadimos los campos de auditoría como lectura
    created_by_name = serializers.ReadOnlyField(source='created_by.username')
    updated_by_name = serializers.ReadOnlyField(source='updated_by.username')

    class Meta:
        model = Node
        fields = [
            'id', 'title', 'parent', 'children', 
            'created_at', 'created_by_name', 'updated_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'created_by_name', 'updated_by_name']

    def validate_title(self, value):
        """Saneamiento y conversión de números a palabras."""
        text_value = str(value).strip()
        if text_value.isdigit():
            lang = self.context.get('language', 'en')
            try:
                text_value = num2words(int(text_value), lang=lang)
            except NotImplementedError:
                text_value = num2words(int(text_value), lang='en')
        return text_value

    def get_children(self, obj):
        """Lógica de profundidad dinámica filtrando nodos borrados."""
        max_depth = self.context.get('max_depth', 0)
        current_depth = self.context.get('current_depth', 0)

        if current_depth < max_depth:
            # IMPORTANTE: Filtrar por is_deleted=False para no mostrar nodos borrados
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
        """Validaciones de integridad y unicidad."""
        title = data.get('title', getattr(self.instance, 'title', None))
        parent = data.get('parent', getattr(self.instance, 'parent', None))

        # 1. Validación de Unicidad por Nivel (Solo contra nodos NO borrados)
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

        # 2. Validación de auto-referencia
        if self.instance and parent and parent.pk == self.instance.pk:
            raise serializers.ValidationError({
                "parent": "Un nodo no puede ser su propio padre."
            })

        return data

    def get_created_at(self, obj):
        """Conversión de zona horaria dinámica."""
        tz_name = self.context.get('user_timezone', 'UTC')
        try:
            user_tz = pytz.timezone(tz_name)
            local_dt = obj.created_at.astimezone(user_tz)
            return local_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
        except Exception:
            return obj.created_at.isoformat()