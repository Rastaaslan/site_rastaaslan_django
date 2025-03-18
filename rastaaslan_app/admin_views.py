"""
admin_views.py - Vues personnalisées pour l'administration Django
"""
import platform
import django
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db import connection
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Count, Q
from datetime import timedelta

from rastaaslan_app.models import (
    Video, ForumCategory, ForumTopic, ForumPost, 
    UserProfile, PostReaction
)

@staff_member_required
def admin_dashboard(request):
    """
    Dashboard personnalisé pour remplacer la page d'accueil de l'admin Django
    """
    # Statistiques principales
    video_count = Video.objects.count()
    user_count = User.objects.count()
    topic_count = ForumTopic.objects.count()
    post_count = ForumPost.objects.count()
    
    # Récupérer les informations sur la base de données
    db_engine = connection.vendor
    db_name = connection.settings_dict['NAME']
    database_info = f"{db_engine} ({db_name})"
    
    # Version de Python et Django
    python_version = platform.python_version()
    django_version = django.get_version()
    
    # Activité récente (30 derniers jours)
    last_30_days = timezone.now() - timedelta(days=30)
    
    # Récupérer l'activité récente
    recent_activities = []
    
    # Messages récents du forum
    recent_posts = ForumPost.objects.select_related('author', 'topic').order_by('-created_at')[:5]
    for post in recent_posts:
        recent_activities.append({
            'type': 'post',
            'title': f"Message dans \"{post.topic.title}\"",
            'user': post.author.username if post.author else "Utilisateur supprimé",
            'timestamp': post.created_at,
            'url': f"/admin/rastaaslan_app/forumpost/{post.id}/change/"
        })
    
    # Sujets récents du forum
    recent_topics = ForumTopic.objects.select_related('author', 'category').order_by('-created_at')[:5]
    for topic in recent_topics:
        recent_activities.append({
            'type': 'topic',
            'title': f"Nouveau sujet : {topic.title}",
            'user': topic.author.username if topic.author else "Utilisateur supprimé",
            'timestamp': topic.created_at,
            'url': f"/admin/rastaaslan_app/forumtopic/{topic.id}/change/"
        })
    
    # Vidéos récemment ajoutées
    recent_videos = Video.objects.order_by('-created_at')[:5]
    for video in recent_videos:
        recent_activities.append({
            'type': 'video',
            'title': f"Vidéo ajoutée : {video.title}",
            'user': None,
            'timestamp': video.created_at,
            'url': f"/admin/rastaaslan_app/video/{video.id}/change/"
        })
    
    # Utilisateurs récemment inscrits
    recent_users = User.objects.order_by('-date_joined')[:5]
    for user in recent_users:
        recent_activities.append({
            'type': 'user',
            'title': f"Nouvel utilisateur : {user.username}",
            'user': None,
            'timestamp': user.date_joined,
            'url': f"/admin/auth/user/{user.id}/change/"
        })
    
    # Trier par date décroissante
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:10]  # Limiter à 10 éléments
    
    # Enrichir les applications et modèles avec des statistiques
    app_list = request.admin_site.get_app_list(request)
    
    # Comptes par modèle
    model_counts = {
        'Video': video_count,
        'User': user_count,
        'ForumTopic': topic_count,
        'ForumPost': post_count,
        'UserProfile': UserProfile.objects.count(),
        'ForumCategory': ForumCategory.objects.count(),
        'PostReaction': PostReaction.objects.count(),
    }
    
    # Ajouter des icônes pour les applications
    app_icons = {
        'rastaaslan_app': 'fas fa-dragon',
        'auth': 'fas fa-users-cog',
        'admin': 'fas fa-tools',
        'contenttypes': 'fas fa-database',
        'sessions': 'fas fa-key',
    }
    
    # Enrichir les applications avec des icônes et des statistiques
    for app in app_list:
        app['app_icon'] = app_icons.get(app['app_label'], 'fas fa-folder')
        
        # Ajouter les statistiques aux modèles
        for model in app['models']:
            model_name = model['object_name']
            if model_name in model_counts:
                model['count'] = model_counts[model_name]
    
    context = {
        'title': "Tableau de bord",
        'app_list': app_list,
        'video_count': video_count,
        'user_count': user_count,
        'topic_count': topic_count,
        'post_count': post_count,
        'django_version': django_version,
        'python_version': python_version,
        'database_info': database_info,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'admin/dashboard.html', context)