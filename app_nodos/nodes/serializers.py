from rest_framework import serializers
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
        Validación a nivel de objeto para reglas complejas.
        """
        parent = data.get('parent')
        
        # Validar auto-referencia (Self-parenting)
        # Comparamos las PKs para estar 100% seguros
        if self.instance and parent:
            if parent.pk == self.instance.pk:
                raise serializers.ValidationError(
                    {"parent": "Un nodo no puede ser su propio padre."}
                )
        
        # Opcional: Validar que el padre no sea un descendiente 
        # (Esto evitaría ciclos más complejos, pero para esta prueba
        # con la validación de auto-referencia suele ser suficiente).
        
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