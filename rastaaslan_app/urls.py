from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('live/', views.live_view, name='live'),
    path('vods/', views.vods_view, name='vods'),
    path('clips/', views.clips_view, name='clips'),
    path('video/<str:video_id>/', views.video_detail, name='video_detail'),
]