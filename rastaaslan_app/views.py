from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib import messages
from django.utils.text import slugify
from django.db.models import Count, Q
from django.utils import timezone
from .models import Video, UserProfile, ForumCategory, ForumTopic, ForumPost
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm, 
    UserProfileForm, CustomPasswordChangeForm,
    ForumTopicForm, ForumPostForm
)
from .twitch_utils import make_twitch_api_request, get_twitch_access_token
import requests

# Configuration constante pour le streamer
TWITCH_USER_LOGIN = 'RastaaslanRadal'
TWITCH_USER_ID = '44504078'  # ID utilisateur Twitch du streamer

def home(request):
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
    # Configuration Twitch
    twitch_user = 'RastaaslanRadal'
    
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
    """
    Vue pour afficher les clips avec différents tris possibles.
    Supporte une version simple avec un seul ensemble de clips,
    extensible pour des catégories multiples.
    """
    # Obtenir le paramètre de tri (optionnel)
    sort = request.GET.get('sort', 'recent')  # Par défaut, trier par date
    
    # Récupérer les clips depuis l'API Twitch
    clips_data = make_twitch_api_request('clips', {'broadcaster_id': '44504078'})
    
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
    
    # Récupérer tous les clips de la base de données
    all_clips = Video.objects.filter(video_type='Clip')
    
    # Pour une version plus avancée, vous pourriez implémenter ces différents tris
    # Ici, nous simulons différentes catégories avec le même ensemble de clips
    # Dans une vraie implémentation, vous utiliseriez des requêtes différentes
    
    """
    # Clips triés par date (les plus récents)
    recent_clips = all_clips.order_by('-created_at')
    
    # Clips triés par popularité (simulation - à remplacer par votre logique)
    popular_clips = all_clips.order_by('?')  # Ordre aléatoire pour simuler
    """
    
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
        return redirect('rastaaslan_app:home')
        
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
        
        return redirect('rastaaslan_app:home')
    except Exception as e:
        print(f"Erreur lors de l'authentification Twitch : {e}")
        return redirect('rastaaslan_app:home')

# ======== User Account Views ========

def register(request):
    """Vue pour l'inscription d'un nouvel utilisateur"""
    if request.user.is_authenticated:
        return redirect('rastaaslan_app:home')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Connecter l'utilisateur après l'inscription
            login(request, user)
            messages.success(request, f"Compte créé avec succès ! Bienvenue {user.username}.")
            return redirect('rastaaslan_app:home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'rastaaslan_app/auth/register.html', {'form': form})

def login_view(request):
    """Vue pour la connexion d'un utilisateur"""
    if request.user.is_authenticated:
        return redirect('rastaaslan_app:home')
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Vous êtes connecté en tant que {username}.")
                # Rediriger vers la page demandée ou la page d'accueil
                next_page = request.GET.get('next', 'rastaaslan_app:home')
                return redirect(next_page)
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe invalide.")
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'rastaaslan_app/auth/login.html', {'form': form})

@login_required
def profile_view(request, username=None):
    """Vue pour afficher un profil utilisateur"""
    if username:
        # Profil d'un autre utilisateur
        user_profile = get_object_or_404(UserProfile, user__username=username)
    else:
        # Profil de l'utilisateur connecté
        user_profile = get_object_or_404(UserProfile, user=request.user)
    
    # Obtenir les statistiques du forum pour l'utilisateur
    forum_stats = {
        'topics_count': ForumTopic.objects.filter(author=user_profile.user).count(),
        'posts_count': ForumPost.objects.filter(author=user_profile.user).count(),
        'recent_topics': ForumTopic.objects.filter(author=user_profile.user).order_by('-created_at')[:5],
        'recent_posts': ForumPost.objects.filter(author=user_profile.user).select_related('topic').order_by('-created_at')[:5]
    }
    
    context = {
        'profile': user_profile,
        'forum_stats': forum_stats,
    }
    
    return render(request, 'rastaaslan_app/auth/profile.html', context)

@login_required
def edit_profile(request):
    """Vue pour modifier son profil utilisateur"""
    profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre profil a été mis à jour avec succès !")
            return redirect('rastaaslan_app:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'rastaaslan_app/auth/edit_profile.html', {'form': form})

@login_required
def change_password(request):
    """Vue pour changer son mot de passe"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Maintenir la session active après le changement de mot de passe
            update_session_auth_hash(request, user)
            messages.success(request, "Votre mot de passe a été changé avec succès !")
            return redirect('rastaaslan_app:profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'rastaaslan_app/auth/change_password.html', {'form': form})

# ======== Forum Views ========

def forum_home(request):
    """Vue pour la page d'accueil du forum"""
    categories = ForumCategory.objects.all().order_by('order')
    
    # Enrichir les catégories avec des statistiques
    for category in categories:
        category.topics_count = category.topics.count()
        category.posts_count = ForumPost.objects.filter(topic__category=category).count()
        # Dernier message
        last_post = ForumPost.objects.filter(topic__category=category).order_by('-created_at').first()
        category.last_post = last_post
    
    # Statistiques globales du forum
    stats = {
        'topics_count': ForumTopic.objects.count(),
        'posts_count': ForumPost.objects.count(),
        'users_count': UserProfile.objects.count(),
        'latest_user': UserProfile.objects.order_by('-date_joined').first() if UserProfile.objects.exists() else None,
    }
    
    context = {
        'categories': categories,
        'stats': stats,
    }
    
    return render(request, 'rastaaslan_app/forum/forum_home.html', context)

def forum_category(request, category_slug):
    """Vue pour afficher les sujets d'une catégorie"""
    category = get_object_or_404(ForumCategory, slug=category_slug)
    
    # Démarrer avec une requête de base pour obtenir tous les sujets de cette catégorie
    topics_queryset = ForumTopic.objects.filter(category=category)
    
    # Filtrer par recherche si un terme est fourni
    search_query = request.GET.get('q', '')
    if search_query:
        topics_queryset = topics_queryset.filter(
            Q(title__icontains=search_query) | Q(content__icontains=search_query)
        )
    
    # Appliquer les relations et le tri
    topics = topics_queryset.select_related('author', 'category').order_by('-is_pinned', '-updated_at')
    
    # Ajouter des informations additionnelles pour chaque sujet
    for topic in topics:
        topic.reply_count = topic.posts.count() - 1  # Exclut le post initial
        topic.last_post = topic.posts.order_by('-created_at').first()
    
    # Pagination
    paginator = Paginator(topics, 20)  # 20 sujets par page
    page = request.GET.get('page')
    topics_page = paginator.get_page(page)
    
    context = {
        'category': category,
        'topics': topics_page,
        'search_query': search_query,
    }
    
    return render(request, 'rastaaslan_app/forum/forum_category.html', context)

def forum_topic(request, category_slug, topic_slug):
    """Vue pour afficher un sujet et ses messages"""
    topic = get_object_or_404(
        ForumTopic.objects.select_related('author', 'category'),
        category__slug=category_slug,
        slug=topic_slug
    )
    
    # Incrémenter le compteur de vues
    topic.increment_views()
    
    # Obtenir tous les messages du sujet avec leurs auteurs
    posts = topic.posts.select_related('author').order_by('created_at')
    
    # Formulaire pour répondre (seulement si le sujet n'est pas verrouillé)
    form = None
    if request.user.is_authenticated and not topic.is_locked:
        if request.method == 'POST':
            form = ForumPostForm(request.POST)
            if form.is_valid():
                post = form.save(commit=False)
                post.topic = topic
                post.author = request.user
                post.save()
                messages.success(request, "Votre réponse a été publiée.")
                return redirect(topic.get_absolute_url())
        else:
            form = ForumPostForm()
    
    # Pagination
    paginator = Paginator(posts, 15)  # 15 messages par page
    page = request.GET.get('page')
    posts_page = paginator.get_page(page)
    
    context = {
        'topic': topic,
        'posts': posts_page,
        'form': form,
    }
    
    return render(request, 'rastaaslan_app/forum/forum_topic.html', context)

@login_required
def create_topic(request, category_slug=None):
    """Vue pour créer un nouveau sujet"""
    initial_data = {}
    if category_slug:
        category = get_object_or_404(ForumCategory, slug=category_slug)
        initial_data['category'] = category
    
    if request.method == 'POST':
        form = ForumTopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.author = request.user
            
            # Générer le slug à partir du titre
            base_slug = slugify(topic.title)
            slug = base_slug
            counter = 1
            
            # S'assurer que le slug est unique
            while ForumTopic.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            topic.slug = slug
            topic.save()
            
            # Créer le premier message (le contenu du sujet)
            ForumPost.objects.create(
                topic=topic,
                author=request.user,
                content=form.cleaned_data['content']
            )
            
            messages.success(request, "Votre sujet a été créé avec succès !")
            return redirect(topic.get_absolute_url())
    else:
        form = ForumTopicForm(initial=initial_data)
    
    context = {
        'form': form,
        'category_slug': category_slug,
    }
    
    return render(request, 'rastaaslan_app/forum/create_topic.html', context)

@login_required
def edit_post(request, post_id):
    """Vue pour modifier un message"""
    post = get_object_or_404(ForumPost, pk=post_id)
    
    # Vérifier que l'utilisateur est l'auteur du message ou un administrateur
    if post.author != request.user and not request.user.is_staff:
        messages.error(request, "Vous n'êtes pas autorisé à modifier ce message.")
        return redirect(post.topic.get_absolute_url())
    
    # Vérifier que le sujet n'est pas verrouillé (sauf pour les administrateurs)
    if post.topic.is_locked and not request.user.is_staff:
        messages.error(request, "Ce sujet est verrouillé et ne peut pas être modifié.")
        return redirect(post.topic.get_absolute_url())
    
    if request.method == 'POST':
        form = ForumPostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save()
            messages.success(request, "Votre message a été modifié avec succès.")
            return redirect(post.get_absolute_url())
    else:
        form = ForumPostForm(instance=post)
    
    context = {
        'form': form,
        'post': post,
    }
    
    return render(request, 'rastaaslan_app/forum/edit_post.html', context)

@login_required
def delete_post(request, post_id):
    """Vue pour supprimer un message"""
    post = get_object_or_404(ForumPost, pk=post_id)
    topic = post.topic
    
    # Vérifier que l'utilisateur est l'auteur du message ou un administrateur
    if post.author != request.user and not request.user.is_staff:
        messages.error(request, "Vous n'êtes pas autorisé à supprimer ce message.")
        return redirect(topic.get_absolute_url())
    
    # Vérifier que le sujet n'est pas verrouillé (sauf pour les administrateurs)
    if topic.is_locked and not request.user.is_staff:
        messages.error(request, "Ce sujet est verrouillé et ne peut pas être modifié.")
        return redirect(topic.get_absolute_url())
    
    # Si c'est le premier message du sujet, supprimer le sujet entier
    if post == topic.posts.earliest('created_at'):
        if request.user.is_staff or post.author == request.user:
            topic.delete()
            messages.success(request, "Le sujet a été supprimé avec succès.")
            return redirect('rastaaslan_app:forum_category', category_slug=topic.category.slug)
        else:
            messages.error(request, "Vous n'êtes pas autorisé à supprimer ce sujet.")
            return redirect(topic.get_absolute_url())
    
    # Sinon, supprimer uniquement le message
    post.delete()
    messages.success(request, "Votre message a été supprimé avec succès.")
    return redirect(topic.get_absolute_url())

def search_forum(request):
    """Vue pour rechercher dans le forum"""
    query = request.GET.get('q', '')
    
    if len(query) < 3:
        messages.warning(request, "Veuillez entrer au moins 3 caractères pour la recherche.")
        return redirect('rastaaslan_app:forum_home')
    
    # Rechercher dans les titres et contenus des sujets
    topics = ForumTopic.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query)
    ).select_related('author', 'category').order_by('-created_at')
    
    # Rechercher dans les contenus des messages
    posts = ForumPost.objects.filter(
        content__icontains=query
    ).select_related('author', 'topic', 'topic__category').order_by('-created_at')
    
    # Pagination des résultats
    topics_paginator = Paginator(topics, 10)
    posts_paginator = Paginator(posts, 10)
    
    topics_page = topics_paginator.get_page(request.GET.get('topics_page'))
    posts_page = posts_paginator.get_page(request.GET.get('posts_page'))
    
    context = {
        'query': query,
        'topics': topics_page,
        'posts': posts_page,
        'total_results': topics.count() + posts.count()
    }
    
    return render(request, 'rastaaslan_app/forum/search_results.html', context)