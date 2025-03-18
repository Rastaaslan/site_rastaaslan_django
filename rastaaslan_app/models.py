from django.db import models
from django.core.validators import URLValidator
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from markdown import markdown
import bleach
import re


class Video(models.Model):
    """
    Modèle représentant une vidéo Twitch (VOD ou clip).
    
    Attributs:
        title (str): Titre de la vidéo
        video_id (str): Identifiant unique de la vidéo sur Twitch
        video_type (str): Type de vidéo ('VOD' ou 'Clip')
        url (str): URL complète de la vidéo sur Twitch
        thumbnail_url (str): URL de la vignette de la vidéo
        created_at (datetime): Date et heure d'ajout à la base de données
    """
    VIDEO_TYPES = (
        ('VOD', 'VOD'),
        ('Clip', 'Clip'),
    )
    
    title = models.CharField("Titre", max_length=255)
    video_id = models.CharField("ID Twitch", max_length=255, unique=True, 
                               help_text="Identifiant unique de la vidéo sur Twitch")
    video_type = models.CharField("Type", max_length=4, choices=VIDEO_TYPES)
    url = models.URLField("URL", validators=[URLValidator()])
    thumbnail_url = models.URLField("URL de la vignette", validators=[URLValidator()])
    created_at = models.DateTimeField("Date d'ajout", auto_now_add=True)
    
    class Meta:
        verbose_name = "Vidéo"
        verbose_name_plural = "Vidéos"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['video_type', 'created_at']),
            models.Index(fields=['video_id']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        """Retourne l'URL pour accéder à cette vidéo spécifique."""
        return reverse('rastaaslan_app:video_detail', args=[self.video_id])
    
    def get_embed_url(self):
        """Retourne l'URL d'intégration appropriée selon le type de vidéo."""
        if self.video_type == 'Clip':
            return f"https://clips.twitch.tv/embed?clip={self.video_id}"
        else:  # VOD
            return f"https://player.twitch.tv/?video={self.video_id}"
    
    def get_sanitized_title(self):
        """Retourne une version slug du titre pour les URL ou les identifiants."""
        return slugify(self.title)
    
    def get_thumbnail_url_formatted(self, width=320, height=180):
        """
        Retourne l'URL de la vignette avec les dimensions spécifiées.
        Certaines URLs de vignettes Twitch contiennent des placeholders de dimensions.
        """
        if '%{width}' in self.thumbnail_url and '%{height}' in self.thumbnail_url:
            return self.thumbnail_url.replace('%{width}', str(width)).replace('%{height}', str(height))
        return self.thumbnail_url
    
    @classmethod
    def get_latest_videos(cls, video_type=None, limit=5):
        """
        Récupère les dernières vidéos, éventuellement filtrées par type.
        
        Args:
            video_type (str, optional): Type de vidéo ('VOD' ou 'Clip')
            limit (int, optional): Nombre maximum de vidéos à retourner
            
        Returns:
            QuerySet: Liste des vidéos correspondant aux critères
        """
        queryset = cls.objects.all()
        if video_type:
            queryset = queryset.filter(video_type=video_type)
        return queryset.order_by('-created_at')[:limit]


class UserProfile(models.Model):
    """
    Modèle étendant l'utilisateur Django par défaut avec des informations supplémentaires
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.URLField("Avatar", blank=True, null=True, help_text="URL de votre avatar")
    bio = models.TextField("Biographie", blank=True, max_length=500)
    twitch_username = models.CharField("Nom d'utilisateur Twitch", max_length=25, blank=True)
    is_streamer = models.BooleanField("Statut de streamer", default=False)
    date_joined = models.DateTimeField("Date d'inscription", auto_now_add=True)
    
    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"
    
    def __str__(self):
        return f"Profil de {self.user.username}"
    
    def get_absolute_url(self):
        """Retourne l'URL pour accéder à ce profil spécifique."""
        return reverse('rastaaslan_app:profile_user', args=[self.user.username])

    def get_avatar_url(self):
        """Retourne l'URL de l'avatar de l'utilisateur ou une URL par défaut."""
        if self.avatar:
            return self.avatar
        return None  # Le template gère déjà le cas où l'avatar est None

    @property
    def display_name(self):
        """Retourne le nom à afficher pour l'utilisateur."""
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username

    @property
    def activity_score(self):
        """Calcule un score d'activité basé sur les posts et topics."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Posts et topics des 30 derniers jours
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_posts = self.user.forum_posts.filter(created_at__gte=thirty_days_ago).count()
        recent_topics = self.user.forum_topics.filter(created_at__gte=thirty_days_ago).count()
        
        # Un score simple : 1 point par message, 3 points par sujet
        return recent_posts + (recent_topics * 3)

    @property
    def forum_activity(self):
        """Retourne les statistiques d'activité du forum pour cet utilisateur"""
        return {
            'topics_count': self.user.forum_topics.count(),
            'posts_count': self.user.forum_posts.count()
        }

class ForumCategory(models.Model):
    """
    Modèle pour les catégories du forum
    """
    name = models.CharField("Nom", max_length=100)
    slug = models.SlugField("Slug", unique=True)
    description = models.TextField("Description", blank=True)
    icon = models.CharField("Icône Font Awesome", max_length=50, blank=True, 
                           help_text="Classe CSS de l'icône Font Awesome (ex: fas fa-gamepad)")
    order = models.IntegerField("Ordre d'affichage", default=0)
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    
    class Meta:
        verbose_name = "Catégorie du forum"
        verbose_name_plural = "Catégories du forum"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('rastaaslan_app:forum_category', args=[self.slug])
    
    def get_topic_count(self):
        return self.topics.count()
    
    def get_post_count(self):
        return ForumPost.objects.filter(topic__category=self).count()
    
    def get_last_post(self):
        return ForumPost.objects.filter(topic__category=self).order_by('-created_at').first()

    def save(self, *args, **kwargs):
        # Générer un slug automatiquement si non fourni
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ForumTopic(models.Model):
    """
    Modèle pour les sujets du forum
    """
    title = models.CharField("Titre", max_length=255)
    slug = models.SlugField("Slug", max_length=255, unique=True)
    category = models.ForeignKey(ForumCategory, on_delete=models.CASCADE, related_name='topics')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='forum_topics')
    content = models.TextField("Contenu")
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de mise à jour", auto_now=True)
    is_pinned = models.BooleanField("Épinglé", default=False)
    is_locked = models.BooleanField("Verrouillé", default=False)
    views_count = models.PositiveIntegerField("Nombre de vues", default=0)
    
    class Meta:
        verbose_name = "Sujet de forum"
        verbose_name_plural = "Sujets de forum"
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['category', 'created_at']),
            models.Index(fields=['is_pinned', 'created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            
            # Assurer l'unicité du slug
            counter = 1
            original_slug = self.slug
            while ForumTopic.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
                
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('rastaaslan_app:forum_topic', args=[self.category.slug, self.slug])
    
    def get_post_count(self):
        # Le compte inclut le post initial
        return self.posts.count()
    
    def get_last_post(self):
        return self.posts.order_by('-created_at').first()
    
    def increment_views(self):
        # Note: Cette méthode est remplacée par une approche plus sûre avec F() dans les vues
        self.views_count += 1
        self.save(update_fields=['views_count'])
        
   
    def reply_count(self):
        """Nombre de réponses (excluant le post initial)"""
        count = self.posts.count() - 1
        return max(0, count)  # Assurer que le résultat n'est jamais négatif

    def has_unread_posts(self, user):
        """Vérifie si un utilisateur a des messages non lus dans ce sujet"""
        if not user.is_authenticated:
            return False
            
        # Vérifier si l'utilisateur a déjà consulté ce sujet
        topic_view = UserTopicView.objects.filter(user=user, topic=self).first()
        if not topic_view:
            return True  # Jamais consulté = non lu
            
        # Vérifier s'il y a des nouveaux messages depuis la dernière consultation
        return self.posts.filter(created_at__gt=topic_view.last_viewed).exists()


class UserTopicView(models.Model):
    """Garde une trace de quand un utilisateur a vu un sujet"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topic_views')
    topic = models.ForeignKey(ForumTopic, on_delete=models.CASCADE, related_name='user_views')
    last_viewed = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'topic')
        verbose_name = "Vue de sujet par utilisateur"
        verbose_name_plural = "Vues de sujets par utilisateurs"
        
    def __str__(self):
        return f"{self.user.username} - {self.topic.title}"


class ForumPost(models.Model):
    """
    Modèle pour les messages du forum
    """
    topic = models.ForeignKey(ForumTopic, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='forum_posts')
    content = models.TextField("Contenu")
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de mise à jour", auto_now=True)
    is_edited = models.BooleanField("Édité", default=False)
    mentioned_users = models.ManyToManyField(User, related_name='post_mentions', blank=True, verbose_name="Utilisateurs mentionnés")
    
    class Meta:
        verbose_name = "Message du forum"
        verbose_name_plural = "Messages du forum"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['topic', 'created_at']),
        ]
    
    def __str__(self):
        return f"Message de {self.author.username if self.author else 'utilisateur supprimé'} dans {self.topic.title}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # Marquer comme édité si ce n'est pas une création
        if self.pk and not self.is_edited:
            self.is_edited = True
        
        super().save(*args, **kwargs)
        
        # Traiter les mentions
        if is_new or self.is_edited:
            self.process_mentions()
        
        # Mettre à jour la date de mise à jour du sujet
        if self.topic:
            # Utiliser update pour éviter les problèmes de concurrence
            ForumTopic.objects.filter(pk=self.topic.pk).update(updated_at=timezone.now())
    
    def get_absolute_url(self):
        return f"{self.topic.get_absolute_url()}#post-{self.id}"

    @property
    def is_first_post(self):
        """Vérifie si ce post est le premier du sujet"""
        return self == self.topic.posts.order_by('created_at').first()
        
    @property
    def content_html(self):
        """Convertit le contenu Markdown en HTML sécurisé"""
        allowed_tags = [
            'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li',
            'ol', 'ul', 'p', 'strong', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'pre', 'span', 'img', 'br', 'hr'
        ]
        allowed_attrs = {
            'a': ['href', 'title', 'rel'],
            'img': ['src', 'alt', 'title', 'width', 'height']
        }
        
        html = markdown(self.content, extensions=['extra', 'nl2br', 'sane_lists'])
        clean_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)
        return clean_html
        
    def process_mentions(self):
        """Extrait et traite les mentions (@username)"""
        mention_pattern = r'@(\w+)'
        usernames = re.findall(mention_pattern, self.content)
        
        # Effacer les anciennes mentions
        self.mentioned_users.clear()
        
        # Ajouter les nouvelles mentions
        for username in set(usernames):  # Utiliser un set pour éviter les doublons
            try:
                user = User.objects.get(username=username)
                self.mentioned_users.add(user)
                # Envoyer notification (géré par le système de notifications)
            except User.DoesNotExist:
                pass


class PostReaction(models.Model):
    """Réactions sur les messages du forum (like, merci, etc.)"""
    REACTION_TYPES = [
        ('like', '👍 Like'),
        ('thanks', '🙏 Merci'),
        ('funny', '😂 Drôle'),
        ('insightful', '💡 Pertinent'),
    ]
    
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_reactions')
    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('post', 'user', 'reaction_type')
        verbose_name = "Réaction à un message"
        verbose_name_plural = "Réactions aux messages"
        
    def __str__(self):
        return f"{self.user.username} a réagi avec {self.get_reaction_type_display()} au message de {self.post.author.username}"