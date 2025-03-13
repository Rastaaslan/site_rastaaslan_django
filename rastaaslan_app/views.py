import requests
from django.shortcuts import render, get_object_or_404
from .models import Video

def home(request):
    return render(request, 'rastaaslan_app/home.html')

def live_view(request):
    twitch_user = 'RastaaslanRadal'
    client_id = '3nnjhncyln9wija7vanfqf7lhsedh2'
    client_secret = 'hvbs7v88ckuov3t4brbxvl1bacpyhk'

    # Obtenir un token d'accès
    token_url = 'https://id.twitch.tv/oauth2/token'
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    token_response = requests.post(token_url, data=token_data)
    access_token = token_response.json().get('access_token')

    if not access_token:
        print("Erreur d'authentification :", token_response.json())
        return render(request, 'rastaaslan_app/live.html', {'error': 'Erreur d\'authentification avec l\'API Twitch.'})

    # Obtenir les informations du live
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}'
    }
    stream_url = f'https://api.twitch.tv/helix/streams?user_login={twitch_user}'
    stream_response = requests.get(stream_url, headers=headers)
    stream_data = stream_response.json().get('data', [])

    context = {
        'stream_data': stream_data,
    }
    return render(request, 'rastaaslan_app/live.html', context)

def vods_view(request):
    twitch_user = 'RastaaslanRadal'
    client_id = '3nnjhncyln9wija7vanfqf7lhsedh2'
    client_secret = 'hvbs7v88ckuov3t4brbxvl1bacpyhk'

    # Obtenir un token d'accès
    token_url = 'https://id.twitch.tv/oauth2/token'
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    token_response = requests.post(token_url, data=token_data)
    access_token = token_response.json().get('access_token')

    if not access_token:
        print("Erreur d'authentification :", token_response.json())
        return render(request, 'rastaaslan_app/vods.html', {'error': 'Erreur d\'authentification avec l\'API Twitch.'})

    # Obtenir les VODs
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}'
    }
    vods_url = f'https://api.twitch.tv/helix/videos?user_id=44504078'
    vods_response = requests.get(vods_url, headers=headers)
    vods_data = vods_response.json().get('data', [])

    # Sauvegarder les VODs dans la base de données avec les vignettes
    for vod in vods_data:
        Video.objects.update_or_create(
            video_id=vod['id'],
            defaults={
                'title': vod['title'],
                'video_type': 'VOD',
                'url': vod['url'],
                'thumbnail_url': vod['thumbnail_url']
            }
        )

    videos = Video.objects.filter(video_type='VOD')
    context = {
        'videos': videos
    }
    return render(request, 'rastaaslan_app/vods.html', context)

def clips_view(request):
    twitch_user = 'RastaaslanRadal'
    client_id = '3nnjhncyln9wija7vanfqf7lhsedh2'
    client_secret = 'hvbs7v88ckuov3t4brbxvl1bacpyhk'

    # Obtenir un token d'accès
    token_url = 'https://id.twitch.tv/oauth2/token'
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    token_response = requests.post(token_url, data=token_data)
    access_token = token_response.json().get('access_token')

    if not access_token:
        print("Erreur d'authentification :", token_response.json())
        return render(request, 'rastaaslan_app/clips.html', {'error': 'Erreur d\'authentification avec l\'API Twitch.'})

    # Obtenir les clips
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}'
    }
    clips_url = f'https://api.twitch.tv/helix/clips?broadcaster_id=44504078'
    clips_response = requests.get(clips_url, headers=headers)
    clips_data = clips_response.json().get('data', [])

    # Sauvegarder les clips dans la base de données avec les vignettes
    for clip in clips_data:
        Video.objects.update_or_create(
            video_id=clip['id'],
            defaults={
                'title': clip['title'],
                'video_type': 'Clip',
                'url': clip['url'],
                'thumbnail_url': clip['thumbnail_url']
            }
        )

    videos = Video.objects.filter(video_type='Clip')
    context = {
        'videos': videos
    }
    return render(request, 'rastaaslan_app/clips.html', context)

def video_detail(request, video_id):
    video = get_object_or_404(Video, video_id=video_id)
    similar_videos = Video.objects.filter(video_type=video.video_type).exclude(pk=video.pk)[:5]
    context = {
        'video': video,
        'similar_videos': similar_videos
    }
    return render(request, 'rastaaslan_app/video_detail.html', context)