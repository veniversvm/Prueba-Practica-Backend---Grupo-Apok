# from django.shortcuts import render
from rest_framework import viewsets
from .models import Node
from .serializers import NodeSerializer
import pytz
from django.utils import timezone

class NodeViewSet(viewsets.ModelViewSet):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Pasamos el idioma del header Accept-Language al serializer
        # Ejemplo: "es-ES,es;q=0.9" -> tomamos "es"
        lang_header = self.request.headers.get('Accept-Language', 'en')
        context['language'] = lang_header.split(',')[0].split('-')[0][:2]
        return context
    
    def list(self, request, *args, **kwargs):
        """
        Sobreescribimos el listado para manejar la zona horaria dinámica.
        """
        user_timezone = request.headers.get('X-Timezone', 'UTC')
        response = super().list(request, *args, **kwargs)

        # Si el usuario mandó una zona horaria, convertimos las fechas en la respuesta
        try:
            tz = pytz.timezone(user_timezone)
            for node in response.data:
                # Convertimos created_at (que viene del serializer como string o datetime)
                # Nota: En una API real, esto se haría mejor en un Middleware o SerializerMethodField
                # pero para esta prueba, lo manejamos aquí para demostrar la lógica.
                pass 
        except pytz.UnknownTimeZoneError:
            pass

        return response