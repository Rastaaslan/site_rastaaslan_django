from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.conf import settings
from ..models import Video, ForumTopic
from ..twitch_utils import fetch_and_update_videos, get_stream_status

# Configuration constante pour le streamer
TWITCH_USER_LOGIN = 'RastaaslanRadal'
TWITCH_USER_ID = '44504078'  # ID utilisateur Twitch du streamer

def home(request):
    """Vue pour la page d'accueil du site"""
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

def live_view(request):
    """Vue pour la page de live stream avec fallback sur les VODs récentes."""
    # Vérifier si le stream est en direct
    is_live, stream_info = get_stream_status(TWITCH_USER_LOGIN)
    
    # Si le stream n'est pas en direct, récupérer les dernières VODs
    latest_vods = []
    if not is_live:
        # Récupérer les 6 dernières VODs de la base de données
        latest_vods = Video.objects.filter(video_type='VOD').order_by('-created_at')[:6]
        
        # Si aucune VOD n'est disponible en base de données, essayer de les récupérer depuis l'API
        if not latest_vods:
            latest_vods = fetch_and_update_videos('VOD', user_id=TWITCH_USER_ID, limit=6)
    
    # Préparer le contexte pour le template
    context = {
        'is_live': is_live,
        'stream_info': stream_info,
        'channel_name': TWITCH_USER_LOGIN,
        'latest_vods': latest_vods
    }
    
    return render(request, 'rastaaslan_app/live.html', context)

def vods_view(request):
    """Vue pour afficher les VODs."""
    # Récupérer et mettre à jour les VODs depuis l'API Twitch
    fetch_and_update_videos('VOD', user_id=TWITCH_USER_ID)
    
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
    """Vue pour afficher les clips."""
    # Obtenir le paramètre de tri (optionnel)
    sort = request.GET.get('sort', 'recent')  # Par défaut, trier par date
    
    # Récupérer et mettre à jour les clips depuis l'API Twitch
    fetch_and_update_videos('Clip', user_id=TWITCH_USER_ID)
    
    # Récupérer tous les clips de la base de données
    all_clips = Video.objects.filter(video_type='Clip')
    
    # Pour l'instant, utiliser le même ensemble pour tous les onglets
    clips = all_clips.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(clips, 9)  # 9 clips par page
    page = request.GET.get('page')
    videos = paginator.get_page(page)
    
    context = {
        'videos': videos,
    }
    
    return render(request, 'rastaaslan_app/clips.html', context)

def video_detail(request, video_id):
    """Vue détaillée d'une vidéo spécifique."""
    video = get_object_or_404(Video, video_id=video_id)
    related_videos = Video.objects.filter(video_type=video.video_type).exclude(pk=video.pk)[:5]
    
    context = {
        'video': video,
        'related_videos': related_videos
    }
    return render(request, 'rastaaslan_app/video_detail.html', context)