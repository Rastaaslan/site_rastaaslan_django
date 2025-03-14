# rastaaslan_app/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from .models import Video
from unittest.mock import patch, MagicMock


class VideoModelTests(TestCase):
    """Tests pour le modèle Video."""
    
    def setUp(self):
        """Configurer les données de test."""
        self.vod = Video.objects.create(
            title="Test VOD",
            video_id="12345678",
            video_type="VOD",
            url="https://www.twitch.tv/videos/12345678",
            thumbnail_url="https://static-cdn.jtvnw.net/cf_vods/12345678/thumbnail.jpg"
        )
        
        self.clip = Video.objects.create(
            title="Test Clip",
            video_id="ClipExample123",
            video_type="Clip",
            url="https://clips.twitch.tv/ClipExample123",
            thumbnail_url="https://clips-media-assets2.twitch.tv/ClipExample123-preview.jpg"
        )
    
    def test_video_creation(self):
        """Tester la création d'une vidéo."""
        self.assertEqual(self.vod.title, "Test VOD")
        self.assertEqual(self.clip.title, "Test Clip")
    
    def test_video_str_representation(self):
        """Tester la représentation en chaîne des objets Video."""
        self.assertEqual(str(self.vod), "Test VOD")
    
    def test_get_absolute_url(self):
        """Tester la méthode get_absolute_url."""
        expected_url = reverse('video_detail', args=[self.vod.video_id])
        self.assertEqual(self.vod.get_absolute_url(), expected_url)
    
    def test_get_embed_url(self):
        """Tester la méthode get_embed_url selon le type de vidéo."""
        self.assertEqual(
            self.vod.get_embed_url(),
            f"https://player.twitch.tv/?video={self.vod.video_id}"
        )
        self.assertEqual(
            self.clip.get_embed_url(),
            f"https://clips.twitch.tv/embed?clip={self.clip.video_id}"
        )
    
    def test_get_thumbnail_url_formatted(self):
        """Tester le formatage des URL des vignettes."""
        # Test avec une URL standard
        self.assertEqual(
            self.vod.get_thumbnail_url_formatted(),
            self.vod.thumbnail_url
        )
        
        # Test avec une URL contenant des placeholders
        self.vod.thumbnail_url = "https://example.com/thumb/%{width}x%{height}/image.jpg"
        self.assertEqual(
            self.vod.get_thumbnail_url_formatted(400, 300),
            "https://example.com/thumb/400x300/image.jpg"
        )


class VideoViewsTests(TestCase):
    """Tests pour les vues liées aux vidéos."""
    
    def setUp(self):
        """Configurer les données et le client de test."""
        self.client = Client()
        self.vod = Video.objects.create(
            title="Test VOD",
            video_id="12345678",
            video_type="VOD",
            url="https://www.twitch.tv/videos/12345678",
            thumbnail_url="https://static-cdn.jtvnw.net/cf_vods/12345678/thumbnail.jpg"
        )
        
        self.clip = Video.objects.create(
            title="Test Clip",
            video_id="ClipExample123",
            video_type="Clip",
            url="https://clips.twitch.tv/ClipExample123",
            thumbnail_url="https://clips-media-assets2.twitch.tv/ClipExample123-preview.jpg"
        )
    
    def test_home_view(self):
        """Tester la vue d'accueil."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rastaaslan_app/home.html')
    
    def test_vods_view(self):
        """Tester la vue des VODs."""
        # Simuler la réponse de l'API Twitch
        with patch('rastaaslan_app.twitch_utils.make_twitch_api_request') as mock_api:
            mock_api.return_value = {'data': []}  # Simuler une réponse vide de l'API
            
            response = self.client.get(reverse('vods'))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'rastaaslan_app/vods.html')
            self.assertIn('videos', response.context)
    
    def test_clips_view(self):
        """Tester la vue des clips."""
        # Simuler la réponse de l'API Twitch
        with patch('rastaaslan_app.twitch_utils.make_twitch_api_request') as mock_api:
            mock_api.return_value = {'data': []}  # Simuler une réponse vide de l'API
            
            response = self.client.get(reverse('clips'))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'rastaaslan_app/clips.html')
            self.assertIn('videos', response.context)
    
    def test_video_detail_view(self):
        """Tester la vue de détail d'une vidéo."""
        response = self.client.get(reverse('video_detail', args=[self.vod.video_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rastaaslan_app/video_detail.html')
        self.assertEqual(response.context['video'], self.vod)
        self.assertIn('related_videos', response.context)
    
    def test_404_for_nonexistent_video(self):
        """Tester qu'une 404 est renvoyée pour une vidéo inexistante."""
        response = self.client.get(reverse('video_detail', args=['nonexistent_id']))
        self.assertEqual(response.status_code, 404)


# Pour une couverture de test plus complète, vous pourriez ajouter :
# - Tests pour les redirections d'authentification Twitch
# - Tests pour la gestion des erreurs d'API
# - Tests d'intégration