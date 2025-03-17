from django.urls import path
from django.contrib.auth import views as auth_views

# Import direct des vues sans utiliser les imports du fichier __init__.py
from .views.video_views import home, live_view, vods_view, clips_view, video_detail
from .views.auth_views import register, login_view, profile_view, edit_profile, change_password, twitch_login, twitch_callback
from .views.forum_views import (
    forum_home, forum_category, forum_topic, create_topic, 
    edit_post, delete_post, search_forum, react_to_post, preview_markdown
)

# Définition du namespace pour l'application
app_name = 'rastaaslan_app'

# Regroupement des URL par type
urlpatterns = [
    # Pages principales
    path('', home, name='home'),
    path('live/', live_view, name='live'),
    path('vods/', vods_view, name='vods'),
    path('clips/', clips_view, name='clips'),
    path('video/<str:video_id>/', video_detail, name='video_detail'),
    
    # Authentification Twitch
    path('auth/twitch/', twitch_login, name='twitch_login'),
    path('auth/twitch/callback', twitch_callback, name='twitch_callback'),
    
    # Authentification utilisateur
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='rastaaslan_app:home'), name='logout'),
    
    # Gestion du profil
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('profile/change-password/', change_password, name='change_password'),
    path('profile/<str:username>/', profile_view, name='profile_user'),
    path('profile/', profile_view, name='profile'),
    
    # Forum
    path('forum/', forum_home, name='forum_home'),
    path('forum/search/', search_forum, name='search_forum'),
    path('forum/create-topic/', create_topic, name='create_topic'),
    path('forum/markdown/preview/', preview_markdown, name='preview_markdown'),
    path('forum/post/<int:post_id>/react/', react_to_post, name='react_to_post'),
    path('forum/post/<int:post_id>/edit/', edit_post, name='edit_post'),
    path('forum/post/<int:post_id>/delete/', delete_post, name='delete_post'),
    path('forum/<slug:category_slug>/create-topic/', create_topic, name='create_topic_category'),
    path('forum/<slug:category_slug>/<slug:topic_slug>/', forum_topic, name='forum_topic'),
    path('forum/<slug:category_slug>/', forum_category, name='forum_category'),
]