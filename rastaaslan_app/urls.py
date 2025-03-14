from django.urls import path
from .views import twitch_login, twitch_callback

urlpatterns = [
    path('auth/twitch/', twitch_login, name='twitch_login'),
    path('auth/twitch/callback', twitch_callback, name='twitch_callback'),
    path('', views.home, name='home'),
    path('live/', views.live_view, name='live'),
    path('vods/', views.vods_view, name='vods'),
    path('clips/', views.clips_view, name='clips'),
    path('video/<str:video_id>/', views.video_detail, name='video_detail'),
]