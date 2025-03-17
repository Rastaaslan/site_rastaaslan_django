from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify
from django.db.models import Count, Q, F
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache
from datetime import timedelta
from ..models import ForumCategory, ForumTopic, ForumPost, UserProfile, UserTopicView, PostReaction
from ..forms import ForumTopicForm, ForumPostForm


def check_rate_limit(request, action_type):
    """
    Vérifie si l'utilisateur peut publier selon les limites configurées.
    
    Args:
        request: La requête HTTP
        action_type: Le type d'action ('post' ou 'topic')
        
    Returns:
        bool: True si l'utilisateur peut poursuivre, False s'il a dépassé les limites
    """
    if request.user.is_staff:
        return True  # Pas de limite pour le staff
    
    # Récupérer les paramètres de configuration
    rate_limits = getattr(settings, 'FORUM_RATE_LIMIT', {
        'posts_per_day': 50,
        'topics_per_day': 10,
        'posts_per_hour': 20,
        'consecutive_posts_wait': 30,  # secondes
    })
    
    user_id = request.user.id
    now = timezone.now()
    
    if action_type == 'post':
        # Vérifier les posts consécutifs
        last_post_time = cache.get(f'last_post_time_{user_id}')
        if last_post_time:
            time_since_last = (now - last_post_time).total_seconds()
            if time_since_last < rate_limits.get('consecutive_posts_wait', 30):
                return False
                
        # Vérifier les posts par heure
        hour_posts = ForumPost.objects.filter(
            author=request.user, 
            created_at__gte=now - timedelta(hours=1)
        ).count()
        if hour_posts >= rate_limits.get('posts_per_hour', 20):
            return False
            
        # Vérifier les posts par jour
        day_posts = ForumPost.objects.filter(
            author=request.user, 
            created_at__gte=now - timedelta(days=1)
        ).count()
        if day_posts >= rate_limits.get('posts_per_day', 50):
            return False
            
        # Mettre à jour le cache
        cache.set(f'last_post_time_{user_id}', now, 3600)
        return True
        
    elif action_type == 'topic':
        # Vérifier les topics par jour
        day_topics = ForumTopic.objects.filter(
            author=request.user, 
            created_at__gte=now - timedelta(days=1)
        ).count()
        if day_topics >= rate_limits.get('topics_per_day', 10):
            return False
        return True
    
    return True


def forum_home(request):
    """Vue pour la page d'accueil du forum"""
    # Utilisation de values() et annotate pour optimiser les requêtes
    categories = ForumCategory.objects.all().order_by('order')
    
    # Requête optimisée pour récupérer les statistiques
    categories_with_stats = categories.annotate(
        topics_count=Count('topics', distinct=True),
        posts_count=Count('topics__posts', distinct=True)
    )
    
    # Requête pour obtenir le dernier message par catégorie
    latest_posts = {}
    for category in categories:
        latest_post = ForumPost.objects.filter(
            topic__category=category
        ).order_by('-created_at').select_related('author', 'topic').first()
        latest_posts[category.id] = latest_post
    
    # Statistiques globales (optimisées)
    stats = {
        'topics_count': ForumTopic.objects.count(),
        'posts_count': ForumPost.objects.count(),
        'users_count': UserProfile.objects.count(),
        'latest_user': UserProfile.objects.order_by('-date_joined').first()
    }
    
    context = {
        'categories': categories_with_stats,
        'latest_posts': latest_posts,
        'stats': stats,
    }
    
    return render(request, 'rastaaslan_app/forum/forum_home.html', context)


def forum_category(request, category_slug):
    """Vue pour afficher les sujets d'une catégorie"""
    category = get_object_or_404(ForumCategory, slug=category_slug)
    
    # Récupérer les paramètres de filtrage et tri
    search_query = request.GET.get('q', '')
    sort = request.GET.get('sort', 'latest')  # Par défaut, trier par date décroissante
    show_pinned = request.GET.get('show_pinned', '1') == '1'
    
    # Démarrer avec une requête de base pour obtenir tous les sujets de cette catégorie
    topics_queryset = ForumTopic.objects.filter(category=category)
    
    # Filtrer par recherche si un terme est fourni
    if search_query:
        topics_queryset = topics_queryset.filter(
            Q(title__icontains=search_query) | Q(content__icontains=search_query)
        )
    
    # Appliquer les relations et le tri
    topics_queryset = topics_queryset.select_related('author', 'category')
    
    # Appliquer le tri sélectionné
    if sort == 'activity':
        topics_queryset = topics_queryset.order_by('-updated_at')
    elif sort == 'views':
        topics_queryset = topics_queryset.order_by('-views_count')
    elif sort == 'replies':
        topics_queryset = topics_queryset.annotate(
            replies=Count('posts') - 1
        ).order_by('-replies')
    else:  # 'latest' par défaut
        topics_queryset = topics_queryset.order_by('-created_at')
    
    # Appliquer le filtre des épinglés
    if show_pinned:
        if sort != 'latest':  # Ne pas réordonner si déjà trié par date
            topics_queryset = topics_queryset.order_by('-is_pinned', *topics_queryset.query.order_by)
    
    # Ajouter des informations additionnelles pour chaque sujet
    topics = list(topics_queryset)
    for topic in topics:
        topic.reply_count = topic.posts.count() - 1  # Exclut le post initial
        topic.last_post = topic.posts.order_by('-created_at').first()
        
        # Vérifier si le sujet a des messages non lus pour l'utilisateur connecté
        if request.user.is_authenticated:
            topic.has_unread = topic.has_unread_posts(request.user)
    
    # Pagination
    paginator = Paginator(topics, 20)  # 20 sujets par page
    page = request.GET.get('page')
    topics_page = paginator.get_page(page)
    
    context = {
        'category': category,
        'topics': topics_page,
        'search_query': search_query,
        'sort': sort,
        'show_pinned': show_pinned,
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
    
    # Obtenir tous les messages du sujet avec leurs auteurs et profils
    posts = topic.posts.select_related('author').prefetch_related(
        'author__profile',
        'reactions'  # Précharger les réactions également
    ).order_by('created_at')
    
    # Mettre à jour ou créer l'entrée de vue pour cet utilisateur
    if request.user.is_authenticated:
        UserTopicView.objects.update_or_create(
            user=request.user,
            topic=topic,
            defaults={'last_viewed': timezone.now()}
        )
    
    # Formulaire pour répondre (seulement si le sujet n'est pas verrouillé)
    form = None
    if request.user.is_authenticated and (not topic.is_locked or request.user.is_staff):
        if request.method == 'POST':
            form = ForumPostForm(request.POST)
            if form.is_valid():
                # Vérifier la limite de débit
                if not check_rate_limit(request, 'post'):
                    messages.error(request, "Vous publiez trop rapidement. Veuillez attendre un peu avant de poster à nouveau.")
                    return redirect(topic.get_absolute_url())
                
                post = form.save(commit=False)
                post.topic = topic
                post.author = request.user
                post.save()
                messages.success(request, "Votre réponse a été publiée.")
                
                # Rediriger vers la dernière page si pagination
                last_page = ((posts.count() + 1) // 15) + 1
                if last_page > 1:
                    return redirect(f"{topic.get_absolute_url()}?page={last_page}#post-{post.id}")
                return redirect(f"{topic.get_absolute_url()}#post-{post.id}")
        else:
            form = ForumPostForm()
    
    # Pagination
    paginator = Paginator(posts, 15)  # 15 messages par page
    page = request.GET.get('page')
    posts_page = paginator.get_page(page)
    
    # Préparer les données de réactions pour chaque message
    for post in posts_page:
        # Compteur de chaque type de réaction
        post.reaction_counts = post.reactions.values('reaction_type').annotate(count=Count('id'))
        
        # Réactions de l'utilisateur courant
        if request.user.is_authenticated:
            post.user_reactions = set(post.reactions.filter(
                user=request.user
            ).values_list('reaction_type', flat=True))
        else:
            post.user_reactions = set()
    
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
            # Vérifier la limite de débit
            if not check_rate_limit(request, 'topic'):
                messages.error(request, "Vous avez créé trop de sujets récemment. Veuillez attendre avant d'en créer un nouveau.")
                return redirect('rastaaslan_app:forum_home')
                
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
    post = get_object_or_404(ForumPost.objects.select_related('topic'), pk=post_id)
    
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
        'preview_html': post.content_html,  # Prévisualisation Markdown
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


@login_required
def react_to_post(request, post_id):
    """
    Vue pour ajouter/supprimer une réaction à un message.
    
    Cette vue est appelée en AJAX.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    post = get_object_or_404(ForumPost, pk=post_id)
    reaction_type = request.POST.get('reaction_type')
    
    if reaction_type not in dict(PostReaction.REACTION_TYPES):
        return JsonResponse({'error': 'Type de réaction invalide'}, status=400)
    
    # Vérifier si cette réaction existe déjà
    existing = PostReaction.objects.filter(
        post=post,
        user=request.user,
        reaction_type=reaction_type
    ).first()
    
    if existing:
        # Supprimer la réaction existante (toggle)
        existing.delete()
        action = 'removed'
    else:
        # Ajouter une nouvelle réaction
        PostReaction.objects.create(
            post=post,
            user=request.user,
            reaction_type=reaction_type
        )
        action = 'added'
    
    # Compter les réactions mises à jour
    reaction_counts = PostReaction.objects.filter(post=post).values(
        'reaction_type'
    ).annotate(count=Count('id'))
    
    reaction_data = {r['reaction_type']: r['count'] for r in reaction_counts}
    
    # Récupérer les émojis pour chaque type de réaction
    reaction_emojis = {r_type: r_display.split(' ')[0] for r_type, r_display in PostReaction.REACTION_TYPES}
    
    return JsonResponse({
        'action': action,
        'reactions': reaction_data,
        'reaction_emojis': reaction_emojis,
        'post_id': post.id
    })


@login_required
def preview_markdown(request):
    """Vue pour prévisualiser le contenu Markdown."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    # Créer un post temporaire non sauvegardé pour utiliser la méthode content_html
    content = request.POST.get('content', '')
    temp_post = ForumPost(content=content)
    
    # Renvoyer le HTML généré
    return JsonResponse({
        'html': temp_post.content_html
    })