"""
Services métier pour le forum - Gestion des notifications et autres fonctionnalités
"""
import re
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.urls import reverse


def extract_mentions(content):
    """
    Extrait les noms d'utilisateur mentionnés dans un texte avec @username.
    
    Args:
        content (str): Contenu du message
        
    Returns:
        list: Liste des noms d'utilisateur mentionnés
    """
    mention_pattern = r'@(\w+)'
    return re.findall(mention_pattern, content)


def get_mentioned_users(content):
    """
    Récupère les objets User correspondant aux mentions dans le contenu.
    
    Args:
        content (str): Contenu du message
        
    Returns:
        list: Liste d'objets User correspondant aux mentions
    """
    usernames = extract_mentions(content)
    if not usernames:
        return []
        
    # Dédupliquer les noms d'utilisateur
    unique_usernames = set(usernames)
    
    # Récupérer les utilisateurs correspondants
    return User.objects.filter(username__in=unique_usernames)


def notify_mentioned_users(post, mentioned_users=None):
    """
    Notifie les utilisateurs mentionnés dans un message.
    
    Args:
        post: L'objet ForumPost contenant les mentions
        mentioned_users (optional): Liste d'objets User à notifier
        
    Returns:
        int: Nombre d'utilisateurs notifiés
    """
    if mentioned_users is None:
        mentioned_users = get_mentioned_users(post.content)
    
    # Ne pas notifier l'auteur du message lui-même
    mentioned_users = [user for user in mentioned_users if user != post.author]
    
    # Si aucun utilisateur à notifier, sortir
    if not mentioned_users:
        return 0
    
    # Préparer le contexte pour l'email
    topic_url = settings.SITE_URL + post.get_absolute_url() if hasattr(settings, 'SITE_URL') else post.get_absolute_url()
    
    for user in mentioned_users:
        # Construire le sujet et le contenu de l'email
        subject = f"Vous avez été mentionné par {post.author.username} sur le forum Rastaaslan"
        
        # Contexte pour le template
        context = {
            'user': user,
            'author': post.author,
            'topic_title': post.topic.title,
            'topic_url': topic_url,
            'content_preview': strip_tags(post.content[:150] + ('...' if len(post.content) > 150 else '')),
        }
        
        # Rendu du template HTML
        html_message = render_to_string('rastaaslan_app/emails/mention_notification.html', context)
        
        # Version texte simple
        plain_message = strip_tags(html_message)
        
        # Envoi de l'email (si EMAIL_BACKEND est configuré)
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=True  # Éviter les erreurs si la configuration email n'est pas complète
            )
        except Exception as e:
            # Logger l'erreur ici si nécessaire
            print(f"Erreur lors de l'envoi de la notification à {user.email}: {e}")
    
    return len(mentioned_users)


def process_post_reactions(post):
    """
    Traite les réactions à un message et retourne les données formatées.
    
    Args:
        post: L'objet ForumPost
        
    Returns:
        dict: Dictionnaire avec les compteurs de réactions
    """
    from ..models import PostReaction
    
    # Récupérer toutes les réactions groupées par type
    reaction_counts = PostReaction.objects.filter(post=post).values(
        'reaction_type'
    ).annotate(count=Count('id'))
    
    # Convertir en dictionnaire
    reaction_data = {r['reaction_type']: r['count'] for r in reaction_counts}
    
    # Préparer les données pour le template
    reactions = []
    for reaction_type, reaction_display in PostReaction.REACTION_TYPES:
        if reaction_type in reaction_data:
            emoji = reaction_display.split(' ')[0]
            reactions.append({
                'type': reaction_type,
                'emoji': emoji,
                'count': reaction_data.get(reaction_type, 0),
            })
    
    return reactions