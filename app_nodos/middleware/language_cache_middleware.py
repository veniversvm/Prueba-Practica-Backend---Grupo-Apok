# app_nodos/middleware/language_cache_middleware.py
from django.utils.deprecation import MiddlewareMixin


class LanguageTimezoneAwareCacheMiddleware(MiddlewareMixin):
    """
    Middleware que agrega headers Vary para cache diferenciado por idioma y timezone.
    """
    
    def process_response(self, request, response):
        # Solo procesar requests GET a endpoints de nodos
        if (request.method == 'GET' and 
            request.path.startswith('/api/nodes/') and
            response.status_code == 200):
            
            # Agregar headers Vary si no existen
            vary_headers = set()
            
            # Headers existentes
            if 'Vary' in response:
                existing = response['Vary']
                if ',' in existing:
                    vary_headers.update([h.strip() for h in existing.split(',')])
                else:
                    vary_headers.add(existing.strip())
            
            # Agregar headers importantes para cache
            vary_headers.add('Accept-Language')
            vary_headers.add('Time-Zone')
            vary_headers.add('X-Timezone')  # Alternativo
            
            # Actualizar header Vary
            response['Vary'] = ', '.join(sorted(vary_headers))
        
        return response