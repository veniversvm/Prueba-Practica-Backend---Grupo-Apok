# middleware/timezone_middleware.py
import pytz
from django.utils import timezone as django_timezone
from django.utils.deprecation import MiddlewareMixin

class TimezoneMiddleware(MiddlewareMixin):
    """
    Middleware para activar la zona horaria del usuario en cada request.
    """
    
    def process_request(self, request):
        tz_name = 'UTC'  # Por defecto
        
        # Buscar zona horaria en headers
        timezone_headers = ['Time-Zone', 'X-Timezone', 'Timezone', 'X-Time-Zone']
        
        for header_name in timezone_headers:
            header_value = request.headers.get(header_name)
            if header_value:
                tz_name = header_value.strip()
                break
        
        # Normalizar zona horaria
        tz_name = self.normalize_timezone(tz_name)
        
        # Validar y activar zona horaria
        if tz_name in pytz.all_timezones:
            try:
                user_tz = pytz.timezone(tz_name)
                django_timezone.activate(user_tz)
                request.user_timezone = tz_name
            except Exception:
                django_timezone.activate(pytz.UTC)
                request.user_timezone = 'UTC'
        else:
            django_timezone.activate(pytz.UTC)
            request.user_timezone = 'UTC'
    
    def process_response(self, request, response):
        # Asegurarnos de desactivar la zona horaria después del request
        django_timezone.deactivate()
        return response
    
    def normalize_timezone(self, tz_name):
        """Normaliza nombres de zonas horarias."""
        if not tz_name:
            return 'UTC'
        
        tz_name = tz_name.strip()
        
        # Mapeo de abreviaturas comunes
        abbr_map = {
            'EST': 'America/New_York',
            'CST': 'America/Chicago',
            'MST': 'America/Denver',
            'PST': 'America/Los_Angeles',
            'CET': 'Europe/Paris',
            'EET': 'Europe/Bucharest',
            'GMT': 'UTC',
        }
        
        return abbr_map.get(tz_name.upper(), tz_name)