
# nodes/mixins.py
from rest_framework import status
from rest_framework.response import Response

from .serializers import serializers

class ValidateIDMixin:
    """
    Mixin para validar que los IDs sean >= 1.
    """
    
    def validate_id(self, pk):
        """
        Valida que el ID sea un número entero >= 1.
        
        Args:
            pk: El ID a validar
            
        Returns:
            tuple: (is_valid, response_or_error)
        """
        try:
            pk_int = int(pk)
            if pk_int < 1:
                return False, Response(
                    {
                        "error": "El ID debe ser un número positivo mayor o igual a 1.",
                        "code": "invalid_id"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            return True, None
        except (ValueError, TypeError):
            return False, Response(
                {
                    "error": "ID inválido. Debe ser un número entero.",
                    "code": "invalid_id_format"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def initial(self, request, *args, **kwargs):
        """
        Validación inicial para todas las operaciones.
        """
        super().initial(request, *args, **kwargs)
        
        # Solo validar si hay un pk en la URL
        if 'pk' in self.kwargs:
            pk = self.kwargs['pk']
            is_valid, error_response = self.validate_id(pk)
            
            if not is_valid:
                raise serializers.ValidationError(error_response.data)