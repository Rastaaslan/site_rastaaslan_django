import requests
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

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
        # Utiliser logger au lieu de print
        logger.error(f"Erreur lors de la récupération du token Twitch: {e}")
    
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
        logger.error("Impossible d'obtenir un token d'accès Twitch")
        return None
        
    headers = {
        'Client-ID': settings.TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    
    api_url = f'https://api.twitch.tv/helix/{endpoint}'
    
    try:
        # Ajoutez un timeout plus long
        response = requests.get(api_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        # Améliorer le logging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la requête à l'API Twitch ({endpoint}): {e}")
        return None

def fetch_and_update_videos(video_type, user_id=None, username=None, limit=20):
    """
    Récupère les vidéos depuis l'API Twitch et les met à jour en base de données.
    
    Args:
        video_type (str): Type de vidéo ('VOD' ou 'Clip')
        user_id (str, optional): ID utilisateur Twitch
        username (str, optional): Nom d'utilisateur Twitch
        limit (int, optional): Nombre maximum de vidéos à récupérer
    
    Returns:
        QuerySet: Vidéos mises à jour
    """
    from .models import Video  # Import ici pour éviter les imports circulaires
    
    # Valider le type de vidéo
    if video_type not in ('VOD', 'Clip'):
        logger.error(f"Type de vidéo invalide: {video_type}")
        return Video.objects.none()
    
    # Déterminer l'endpoint et les paramètres selon le type
    if video_type == 'VOD':
        endpoint = 'videos'
        params = {'user_id': user_id, 'first': limit}
    else:  # Clip
        endpoint = 'clips'
        params = {'broadcaster_id': user_id, 'first': limit}
    
    # Si username est fourni mais pas user_id, chercher d'abord l'user_id
    if username and not user_id:
        user_data = make_twitch_api_request('users', {'login': username})
        if user_data and user_data.get('data'):
            user_id = user_data['data'][0]['id']
            if video_type == 'VOD':
                params['user_id'] = user_id
            else:
                params['broadcaster_id'] = user_id
        else:
            logger.error(f"Impossible de trouver l'utilisateur Twitch: {username}")
            return Video.objects.none()
    
    # Récupérer les vidéos
    videos_data = make_twitch_api_request(endpoint, params)
    
    # Traiter les données et les sauvegarder
    if videos_data and videos_data.get('data'):
        for video in videos_data['data']:
            # Adapter le traitement selon le type
            if video_type == 'VOD':
                video_id = video['id']
                url = video['url']
                thumbnail_url = video['thumbnail_url'].replace('%{width}', '320').replace('%{height}', '180')
            else:  # Clip
                video_id = video['id']
                url = video['url']
                thumbnail_url = video['thumbnail_url']
            
            # Créer ou mettre à jour la vidéo
            Video.objects.update_or_create(
                video_id=video_id,
                defaults={
                    'title': video['title'],
                    'video_type': video_type,
                    'url': url,
                    'thumbnail_url': thumbnail_url
                }
            )
    
    # Renvoyer les vidéos mises à jour
    return Video.objects.filter(video_type=video_type).order_by('-created_at')

def get_stream_status(username):
    """
    Vérifie si un utilisateur est en direct sur Twitch.
    
    Args:
        username (str): Nom d'utilisateur Twitch
        
    Returns:
        tuple: (is_live, stream_info) où is_live est un booléen et stream_info contient les détails du stream
    """
    stream_data = make_twitch_api_request('streams', {'user_login': username})
    
    is_live = False
    stream_info = None
    
    if stream_data and stream_data.get('data'):
        is_live = True
        stream_info = stream_data['data'][0]
    
    return is_live, stream_info