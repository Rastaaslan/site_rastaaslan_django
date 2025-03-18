import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q

from ..models import UserProfile, ForumTopic, ForumPost, PostReaction
from ..forms import (
    CustomUserCreationForm, CustomAuthenticationForm, 
    UserProfileForm, CustomPasswordChangeForm
)

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
    """
    Vue améliorée pour afficher un profil utilisateur avec :
    - Statistiques détaillées sur l'activité du forum
    - Pagination des messages et sujets récents
    - Catégories les plus actives
    """
    if username is None:
        # Profil de l'utilisateur connecté
        user_profile = get_object_or_404(UserProfile, user=request.user)
    else:
        # Profil d'un autre utilisateur
        user_profile = get_object_or_404(UserProfile, user__username=username)
    
    # Utilisateur dont on affiche le profil
    profile_user = user_profile.user
    
    # Pagination pour les messages et sujets récents
    topics_page = request.GET.get('topics_page', 1)
    posts_page = request.GET.get('posts_page', 1)
    
    # Récupérer tous les sujets et messages pour la pagination
    all_topics = (ForumTopic.objects
        .filter(author=profile_user)
        .select_related('category')
        .order_by('-created_at'))
    
    all_posts = (ForumPost.objects
        .filter(author=profile_user)
        .select_related('topic', 'topic__category')
        .order_by('-created_at'))
    
    # Pagination
    topics_paginator = Paginator(all_topics, 5)  # 5 sujets par page
    posts_paginator = Paginator(all_posts, 5)  # 5 messages par page
    
    try:
        paginated_topics = topics_paginator.page(topics_page)
    except (PageNotAnInteger, EmptyPage):
        paginated_topics = topics_paginator.page(1)
        
    try:
        paginated_posts = posts_paginator.page(posts_page)
    except (PageNotAnInteger, EmptyPage):
        paginated_posts = posts_paginator.page(1)
    
    # Statistiques plus détaillées
    
    # Activité récente (30 derniers jours)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    recent_activity = {
        'topics_count': ForumTopic.objects.filter(author=profile_user, created_at__gte=thirty_days_ago).count(),
        'posts_count': ForumPost.objects.filter(author=profile_user, created_at__gte=thirty_days_ago).count(),
    }
    
    # Catégories les plus actives
    active_categories = (ForumPost.objects
        .filter(author=profile_user)
        .values('topic__category__name', 'topic__category__slug')
        .annotate(count=Count('id'))
        .order_by('-count')[:3])
    
    # Informations sur les réactions reçues
    reactions_received = (PostReaction.objects
        .filter(post__author=profile_user)
        .values('reaction_type')
        .annotate(count=Count('id'))
        .order_by('-count'))
    
    forum_stats = {
        'topics_count': all_topics.count(),
        'posts_count': all_posts.count(),
        'recent_topics': paginated_topics,
        'recent_posts': paginated_posts,
        'recent_activity': recent_activity,
        'active_categories': active_categories,
        'reactions_received': reactions_received,
    }
    
    context = {
        'profile': user_profile,
        'forum_stats': forum_stats,
        'is_own_profile': request.user == profile_user,
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
            return redirect('rastaaslan_app:profile')  # Corrigé
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
            return redirect('rastaaslan_app:profile')  # Corrigé
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'rastaaslan_app/auth/change_password.html', {'form': form})

def twitch_login(request):
    """Vue pour l'authentification via Twitch"""
    auth_url = (
        f"https://id.twitch.tv/oauth2/authorize"
        f"?client_id={settings.TWITCH_CLIENT_ID}"
        f"&redirect_uri={settings.TWITCH_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=chat:edit chat:read"
    )
    return redirect(auth_url)

def twitch_callback(request):
    """Callback pour l'authentification Twitch"""
    code = request.GET.get('code')
    
    if not code:
        messages.error(request, "Erreur lors de l'authentification Twitch.")
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
        
        messages.success(request, "Authentification Twitch réussie.")
        return redirect('rastaaslan_app:home')
    except Exception as e:
        messages.error(request, f"Erreur lors de l'authentification Twitch: {str(e)}")
        return redirect('rastaaslan_app:home')