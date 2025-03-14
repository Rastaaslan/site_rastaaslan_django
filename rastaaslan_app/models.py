from django.db import models
from django.core.validators import URLValidator
from django.utils.text import slugify
from django.urls import reverse


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
        return reverse('video_detail', args=[self.video_id])
    
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