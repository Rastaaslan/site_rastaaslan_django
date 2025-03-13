from django.db import models

class Video(models.Model):
    VIDEO_TYPES = (
        ('VOD', 'VOD'),
        ('Clip', 'Clip'),
    )
    title = models.CharField(max_length=255)
    video_id = models.CharField(max_length=255, unique=True)
    video_type = models.CharField(max_length=4, choices=VIDEO_TYPES)
    url = models.URLField()
    thumbnail_url = models.URLField()  # Ajout du champ pour l'URL de la vignette
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
