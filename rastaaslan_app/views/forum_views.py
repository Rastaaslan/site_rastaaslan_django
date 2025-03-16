from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify
from django.db.models import Count, Q, F
from django.db import transaction
from django.utils import timezone
from ..models import ForumCategory, ForumTopic, ForumPost, UserProfile
from ..forms import ForumTopicForm, ForumPostForm

def forum_home(request):
    """Vue pour la page d'accueil du forum"""
    categories = ForumCategory.objects.all().order_by('order')
    
    # Enrichir les catégories avec des statistiques
    for category in categories:
        category.topics_count = category.topics.count()
        category.posts_count = ForumPost.objects.filter(topic__category=category).count()
        # Dernier message
        category.last_post = ForumPost.objects.filter(topic__category=category).order_by('-created_at').first()
    
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
    
    # Incrémenter le compteur de vues de manière sécurisée
    with transaction.atomic():
        ForumTopic.objects.filter(pk=topic.pk).update(views_count=F('views_count') + 1)
        topic.refresh_from_db()
    
    # Obtenir tous les messages du sujet avec leurs auteurs
    posts = topic.posts.select_related('author').order_by('created_at')
    
    # Formulaire pour répondre (seulement si le sujet n'est pas verrouillé)
    form = None
    if request.user.is_authenticated and (not topic.is_locked or request.user.is_staff):
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
            with transaction.atomic():
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
    
    with transaction.atomic():
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