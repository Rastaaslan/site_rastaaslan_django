from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.conf import settings
from .models import Video
from .twitch_utils import make_twitch_api_request, get_twitch_access_token

# Configuration constante pour le streamer
TWITCH_USER_LOGIN = 'RastaaslanRadal'
TWITCH_USER_ID = '44504078'  # ID utilisateur Twitch du streamer

def home(request):
    # Récupérer les dernières vidéos pour la page d'accueil
    latest_vods = Video.objects.filter(video_type='VOD').order_by('-created_at')[:3]
    latest_clips = Video.objects.filter(video_type='Clip').order_by('-created_at')[:3]
    
    context = {
        'latest_vods': latest_vods,
        'latest_clips': latest_clips
    }
    return render(request, 'rastaaslan_app/home.html', context)

def live_view(request):
    """Vue pour la page de live stream avec fallback sur les VODs récentes."""
    # Configuration Twitch
    twitch_user = 'RastaaslanRadal'
    
    # Utiliser l'utilitaire Twitch pour obtenir un token et faire la requête
    from .twitch_utils import make_twitch_api_request
    
    # Obtenir les informations du stream
    stream_data = make_twitch_api_request(f'streams', {'user_login': twitch_user})
    
    # Vérifier si le stream est en direct
    is_live = False
    stream_info = None
    
    if stream_data and stream_data.get('data'):
        is_live = True
        stream_info = stream_data['data'][0]
    
    # Si le stream n'est pas en direct, récupérer les dernières VODs
    latest_vods = []
    if not is_live:
        # Récupérer les 6 dernières VODs de la base de données
        from .models import Video
        latest_vods = Video.objects.filter(video_type='VOD').order_by('-created_at')[:6]
        
        # Si aucune VOD n'est disponible en base de données, essayer de les récupérer depuis l'API
        if not latest_vods:
            # Utiliser le user_id pour RastaaslanRadal
            user_id = '44504078'
            vods_data = make_twitch_api_request('videos', {'user_id': user_id})
            
            if vods_data and vods_data.get('data'):
                # Enregistrer les VODs en base de données
                for vod in vods_data['data'][:6]:  # Limiter à 6 VODs
                    # Remplacer les paramètres de dimension dans l'URL de la vignette
                    thumbnail_url = vod['thumbnail_url'].replace('%{width}', '320').replace('%{height}', '180')
                    
                    # Créer ou mettre à jour la VOD dans la base de données
                    Video.objects.update_or_create(
                        video_id=vod['id'],
                        defaults={
                            'title': vod['title'],
                            'video_type': 'VOD',
                            'url': vod['url'],
                            'thumbnail_url': thumbnail_url
                        }
                    )
                
                # Récupérer à nouveau les VODs maintenant qu'elles sont enregistrées
                latest_vods = Video.objects.filter(video_type='VOD').order_by('-created_at')[:6]
    
    # Préparer le contexte pour le template
    context = {
        'is_live': is_live,
        'stream_info': stream_info,
        'channel_name': twitch_user,
        'latest_vods': latest_vods
    }
    
    return render(request, 'rastaaslan_app/live.html', context)

def vods_view(request):
    # Récupérer les VODs depuis l'API Twitch
    vods_data = make_twitch_api_request('videos', {'user_id': TWITCH_USER_ID})
    
    # Traiter les données et les sauvegarder
    if vods_data and vods_data.get('data'):
        for vod in vods_data['data']:
            Video.objects.update_or_create(
                video_id=vod['id'],
                defaults={
                    'title': vod['title'],
                    'video_type': 'VOD',
                    'url': vod['url'],
                    'thumbnail_url': vod['thumbnail_url'].replace('%{width}', '320').replace('%{height}', '180')
                }
            )
    
    # Pagination des résultats
    videos_list = Video.objects.filter(video_type='VOD').order_by('-created_at')
    paginator = Paginator(videos_list, 9)  # 9 vidéos par page
    
    page = request.GET.get('page')
    videos = paginator.get_page(page)
    
    context = {
        'videos': videos
    }
    return render(request, 'rastaaslan_app/vods.html', context)

def clips_view(request):
    # Récupérer les clips depuis l'API Twitch
    clips_data = make_twitch_api_request('clips', {'broadcaster_id': TWITCH_USER_ID})
    
    # Traiter les données et les sauvegarder
    if clips_data and clips_data.get('data'):
        for clip in clips_data['data']:
            Video.objects.update_or_create(
                video_id=clip['id'],
                defaults={
                    'title': clip['title'],
                    'video_type': 'Clip',
                    'url': clip['url'],
                    'thumbnail_url': clip['thumbnail_url']
                }
            )
    
    # Pagination des résultats
    clips_list = Video.objects.filter(video_type='Clip').order_by('-created_at')
    paginator = Paginator(clips_list, 9)  # 9 clips par page
    
    page = request.GET.get('page')
    videos = paginator.get_page(page)
    
    context = {
        'videos': videos
    }
    return render(request, 'rastaaslan_app/clips.html', context)

def video_detail(request, video_id):
    video = get_object_or_404(Video, video_id=video_id)
    related_videos = Video.objects.filter(video_type=video.video_type).exclude(pk=video.pk)[:5]
    
    context = {
        'video': video,
        'related_videos': related_videos  # Nom corrigé pour correspondre au template
    }
    return render(request, 'rastaaslan_app/video_detail.html', context)

def twitch_login(request):
    auth_url = (
        f"https://id.twitch.tv/oauth2/authorize"
        f"?client_id={settings.TWITCH_CLIENT_ID}"
        f"&redirect_uri={settings.TWITCH_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=chat:edit chat:read"
    )
    return redirect(auth_url)

def twitch_callback(request):
    code = request.GET.get('code')
    
    if not code:
        # Rediriger vers la page d'accueil avec un message d'erreur
        return redirect('home')
        
    token_url = 'https://id.twitch.tv/oauth2/token'
    token_data = {
        'client_id': settings.TWITCH_CLIENT_ID,
        'client_secret': settings.TWITCH_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': settings.TWITCH_REDIRECT_URI,
    }
    
    try:
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        tokens = response.json()

        # Stocker les tokens dans la session
        request.session['twitch_access_token'] = tokens['access_token']
        request.session['twitch_refresh_token'] = tokens['refresh_token']
        
        return redirect('home')
    except Exception as e:
        print(f"Erreur lors de l'authentification Twitch : {e}")
        return redirect('home')