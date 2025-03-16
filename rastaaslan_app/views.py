import logging
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.conf import settings
from django.core.cache import cache
from ..models import Video, ForumTopic
from ..twitch_utils import fetch_and_update_videos, get_stream_status

# Configuration du logger
logger = logging.getLogger(__name__)

# Configuration constante pour le streamer
TWITCH_USER_LOGIN = 'RastaaslanRadal'
TWITCH_USER_ID = '44504078'  # ID utilisateur Twitch du streamer

def home(request):
    """Vue pour la page d'accueil du site"""
    try:
        # Récupérer les dernières vidéos pour la page d'accueil
        latest_vods = Video.objects.filter(video_type='VOD').order_by('-created_at')[:3]
        latest_clips = Video.objects.filter(video_type='Clip').order_by('-created_at')[:3]
        
        # Récupérer les derniers sujets du forum
        latest_topics = ForumTopic.objects.select_related('category', 'author').order_by('-created_at')[:5]
        
        context = {
            'latest_vods': latest_vods,
            'latest_clips': latest_clips,
            'latest_topics': latest_topics
        }
        return render(request, 'rastaaslan_app/home.html', context)
    except Exception as e:
        logger.error(f"Erreur dans la vue home: {e}")
        # Fournir un contexte minimal en cas d'erreur
        return render(request, 'rastaaslan_app/home.html', {'latest_vods': [], 'latest_clips': [], 'latest_topics': []})

def live_view(request):
    """Vue pour la page de live stream avec fallback sur les VODs récentes."""
    try:
        # Essayer d'abord de récupérer le statut du stream depuis le cache
        cache_key = f"stream_status_{TWITCH_USER_LOGIN}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            is_live, stream_info = cached_data
        else:
            # Si pas en cache, interroger l'API
            is_live, stream_info = get_stream_status(TWITCH_USER_LOGIN)
            # Mettre en cache pour 3 minutes (un délai court car le statut du stream peut changer)
            cache.set(cache_key, (is_live, stream_info), 180)
        
        # Si le stream n'est pas en direct, récupérer les dernières VODs
        latest_vods = []
        if not is_live:
            # Récupérer les 6 dernières VODs de la base de données
            latest_vods = Video.objects.filter(video_type='VOD').order_by('-created_at')[:6]
            
            # Si aucune VOD n'est disponible en base de données, essayer de les récupérer depuis l'API
            if not latest_vods.exists():
                try:
                    latest_vods = fetch_and_update_videos('VOD', user_id=TWITCH_USER_ID, limit=6)
                except Exception as api_error:
                    logger.error(f"Erreur lors de la récupération des VODs depuis l'API: {api_error}")
                    latest_vods = []
        
        # Préparer le contexte pour le template
        context = {
            'is_live': is_live,
            'stream_info': stream_info,
            'channel_name': TWITCH_USER_LOGIN,
            'latest_vods': latest_vods
        }
        
        return render(request, 'rastaaslan_app/live.html', context)
    except Exception as e:
        logger.error(f"Erreur dans la vue live_view: {e}")
        # En cas d'erreur, afficher simplement les VODs disponibles
        latest_vods = Video.objects.filter(video_type='VOD').order_by('-created_at')[:6]
        return render(request, 'rastaaslan_app/live.html', {
            'is_live': False,
            'stream_info': None,
            'channel_name': TWITCH_USER_LOGIN,
            'latest_vods': latest_vods
        })

def vods_view(request):
    """Vue pour afficher les VODs."""
    try:
        # Récupérer et mettre à jour les VODs depuis l'API Twitch
        # Utilisation d'un cache pour limiter les appels API fréquents
        cache_key = "vods_update_timestamp"
        last_update = cache.get(cache_key)
        
        # Mettre à jour les VODs seulement si la dernière mise à jour date de plus de 30 minutes
        if not last_update:
            try:
                fetch_and_update_videos('VOD', user_id=TWITCH_USER_ID)
                cache.set(cache_key, True, 1800)  # Cache pour 30 minutes
            except Exception as api_error:
                logger.error(f"Erreur lors de la mise à jour des VODs: {api_error}")
        
        # Pagination des résultats
        videos_list = Video.objects.filter(video_type='VOD').order_by('-created_at')
        paginator = Paginator(videos_list, 9)  # 9 vidéos par page
        
        page = request.GET.get('page')
        videos = paginator.get_page(page)
        
        context = {
            'videos': videos
        }
        return render(request, 'rastaaslan_app/vods.html', context)
    except Exception as e:
        logger.error(f"Erreur dans la vue vods_view: {e}")
        # En cas d'erreur, afficher les VODs existantes
        videos_list = Video.objects.filter(video_type='VOD').order_by('-created_at')
        paginator = Paginator(videos_list, 9)
        videos = paginator.get_page(1)  # Page 1 par défaut en cas d'erreur
        return render(request, 'rastaaslan_app/vods.html', {'videos': videos})

def clips_view(request):
    """Vue pour afficher les clips."""
    try:
        # Obtenir le paramètre de tri (optionnel)
        sort = request.GET.get('sort', 'recent')  # Par défaut, trier par date
        
        # Récupérer et mettre à jour les clips depuis l'API Twitch
        # Utilisation d'un cache pour limiter les appels API fréquents
        cache_key = "clips_update_timestamp"
        last_update = cache.get(cache_key)
        
        # Mettre à jour les clips seulement si la dernière mise à jour date de plus de 30 minutes
        if not last_update:
            try:
                fetch_and_update_videos('Clip', user_id=TWITCH_USER_ID)
                cache.set(cache_key, True, 1800)  # Cache pour 30 minutes
            except Exception as api_error:
                logger.error(f"Erreur lors de la mise à jour des clips: {api_error}")
        
        # Récupérer tous les clips de la base de données
        all_clips = Video.objects.filter(video_type='Clip')
        
        # Appliquer le tri en fonction du paramètre
        if sort == 'popular':
            # Ici vous pourriez avoir une logique différente pour les clips populaires
            # Pour l'exemple on utilise le même ordre
            clips = all_clips.order_by('-created_at')
        else:  # 'recent' par défaut
            clips = all_clips.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(clips, 9)  # 9 clips par page
        page = request.GET.get('page')
        videos = paginator.get_page(page)
        
        context = {
            'videos': videos,
        }
        
        return render(request, 'rastaaslan_app/clips.html', context)
    except Exception as e:
        logger.error(f"Erreur dans la vue clips_view: {e}")
        # En cas d'erreur, afficher les clips existants
        all_clips = Video.objects.filter(video_type='Clip').order_by('-created_at')
        paginator = Paginator(all_clips, 9)
        videos = paginator.get_page(1)  # Page 1 par défaut en cas d'erreur
        return render(request, 'rastaaslan_app/clips.html', {'videos': videos})

def video_detail(request, video_id):
    """Vue détaillée d'une vidéo spécifique."""
    try:
        video = get_object_or_404(Video, video_id=video_id)
        # Optimisation avec select_related si nécessaire
        related_videos = Video.objects.filter(video_type=video.video_type).exclude(pk=video.pk)[:5]
        
        context = {
            'video': video,
            'related_videos': related_videos
        }
        return render(request, 'rastaaslan_app/video_detail.html', context)
    except Exception as e:
        logger.error(f"Erreur dans la vue video_detail pour video_id={video_id}: {e}")
        # Rediriger vers une page d'erreur ou vers la liste des vidéos
        return render(request, 'rastaaslan_app/video_detail.html', {
            'error': True,
            'message': "La vidéo demandée n'est pas disponible."
        }, status=404)