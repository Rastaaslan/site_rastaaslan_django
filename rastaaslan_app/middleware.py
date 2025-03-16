import re
from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class SecureRequestMiddleware:
    """
    Middleware pour améliorer la sécurité des requêtes HTTP.
    - Redirection vers HTTPS
    - Ajout des en-têtes de sécurité
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # HTTPS redirect in production
        if not settings.DEBUG and not request.is_secure():
            request_url = request.build_absolute_uri(request.get_full_path())
            secure_url = re.sub(r'^http://', 'https://', request_url)
            return HttpResponsePermanentRedirect(secure_url)
        
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Seulement en production pour éviter les problèmes en développement
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' https://code.jquery.com https://cdn.jsdelivr.net https://stackpath.bootstrapcdn.com 'unsafe-inline'; "
                "style-src 'self' https://stackpath.bootstrapcdn.com https://cdnjs.cloudflare.com 'unsafe-inline'; "
                "font-src 'self' https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https://*.twitch.tv https://*.jtvnw.net; "
                "frame-src https://*.twitch.tv; "
                "connect-src 'self' https://api.twitch.tv; "
            )
        
        return response