import requests
from django.conf import settings
from django.core.cache import cache

def get_twitch_access_token():
    """
    Récupère un token d'accès Twitch à partir de l'API,
    avec mise en cache pour éviter les requêtes répétées.
    """
    # Vérifier si un token est déjà en cache
    cached_token = cache.get('twitch_access_token')
    if cached_token:
        return cached_token

    # Si pas de token en cache, faire une nouvelle requête
    token_url = 'https://id.twitch.tv/oauth2/token'
    token_data = {
        'client_id': settings.TWITCH_CLIENT_ID,
        'client_secret': settings.TWITCH_CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    
    try:
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()  # Lève une exception en cas d'erreur HTTP
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        if access_token:
            # Mettre en cache le token pour 3 heures (temps typique d'expiration - marge de sécurité)
            expires_in = token_data.get('expires_in', 14400)  # Par défaut 4 heures si non spécifié
            cache_time = expires_in - 3600  # 1 heure de marge avant expiration
            cache.set('twitch_access_token', access_token, cache_time)
            
            return access_token
    except requests.RequestException as e:
        # Log l'erreur
        print(f"Erreur lors de la récupération du token Twitch: {e}")
    
    return None

def make_twitch_api_request(endpoint, params=None):
    """
    Effectue une requête authentifiée à l'API Twitch.
    
    Args:
        endpoint (str): Point de terminaison de l'API (sans le préfixe)
        params (dict, optional): Paramètres de requête
        
    Returns:
        dict: Données de réponse JSON ou None en cas d'erreur
    """
    access_token = get_twitch_access_token()
    
    if not access_token:
        return None
        
    headers = {
        'Client-ID': settings.TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    
    api_url = f'https://api.twitch.tv/helix/{endpoint}'
    
    try:
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        # Log l'erreur
        print(f"Erreur lors de la requête à l'API Twitch ({endpoint}): {e}")
        return None