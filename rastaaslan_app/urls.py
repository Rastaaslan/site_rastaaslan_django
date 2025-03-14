from django.urls import path
from . import views

# Définition du namespace pour l'application
app_name = 'rastaaslan_app'

# Regroupement des URL par type
urlpatterns = [
    # Pages principales
    path('', views.home, name='home'),
    path('live/', views.live_view, name='live'),
    path('vods/', views.vods_view, name='vods'),
    path('clips/', views.clips_view, name='clips'),
    path('video/<str:video_id>/', views.video_detail, name='video_detail'),
    
    # Authentification Twitch
    path('auth/twitch/', views.twitch_login, name='twitch_login'),
    path('auth/twitch/callback', views.twitch_callback, name='twitch_callback'),
    
    # API (exemple pour une future extension)
    # path('api/videos/', views.api_videos, name='api_videos'),
]
