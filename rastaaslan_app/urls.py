from django.urls import path
from django.contrib.auth import views as auth_views
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
    
    # Authentification utilisateur
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='rastaaslan_app:home'), name='logout'),
    
    # Gestion du profil
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.profile_view, name='profile_user'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # Forum
    path('forum/', views.forum_home, name='forum_home'),
    path('forum/search/', views.search_forum, name='search_forum'),
    path('forum/create-topic/', views.create_topic, name='create_topic'),
    path('forum/<slug:category_slug>/', views.forum_category, name='forum_category'),
    path('forum/<slug:category_slug>/create-topic/', views.create_topic, name='create_topic_category'),
    path('forum/<slug:category_slug>/<slug:topic_slug>/', views.forum_topic, name='forum_topic'),
    path('forum/post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('forum/post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
]