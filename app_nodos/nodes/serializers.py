from rest_framework import serializers
from .models import Node
from num2words import num2words

class NodeSerializer(serializers.ModelSerializer):
    # Definimos children para poder ver los hijos en el listado (opcional según el requerimiento de depth)
    children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Node
        fields = ['id', 'title', 'parent', 'children', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_title(self, value):
        """
        Saneamiento y Lógica de Negocio:
        1. Limpiar espacios.
        2. Si es número, convertir a palabras.
        """
        text_value = str(value).strip()

        if text_value.isdigit():
            # Extraemos el idioma del contexto (pasado por la vista desde el header)
            lang = self.context.get('language', 'en')
            try:
                # Convertimos el número a palabras en el idioma solicitado
                text_value = num2words(int(text_value), lang=lang)
            except NotImplementedError:
                # Fallback a inglés si el idioma no está soportado por num2words
                text_value = num2words(int(text_value), lang='en')
        
        return text_value

    def validate(self, data):
        """
        Validación a nivel de objeto.
        """
        # Regla: Un nodo no puede ser su propio padre (evitar ciclos)
        if self.instance and data.get('parent') == self.instance:
            raise serializers.ValidationError({"parent": "Un nodo no puede ser su propio padre."})
        return data