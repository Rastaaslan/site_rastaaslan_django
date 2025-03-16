# rastaaslan_app/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Video, UserProfile, ForumCategory, ForumTopic, ForumPost
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
        expected_url = reverse('rastaaslan_app:video_detail', args=[self.vod.video_id])
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
        
        # Test avec des dimensions par défaut
        self.assertEqual(
            self.vod.get_thumbnail_url_formatted(),
            "https://example.com/thumb/320x180/image.jpg"
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
        response = self.client.get(reverse('rastaaslan_app:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rastaaslan_app/home.html')
        self.assertIn('latest_vods', response.context)
        self.assertIn('latest_clips', response.context)
    
    def test_vods_view(self):
        """Tester la vue des VODs."""
        # Simuler la réponse de l'API Twitch
        with patch('rastaaslan_app.twitch_utils.fetch_and_update_videos') as mock_fetch:
            mock_fetch.return_value = Video.objects.filter(video_type='VOD')
            
            response = self.client.get(reverse('rastaaslan_app:vods'))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'rastaaslan_app/vods.html')
            self.assertIn('videos', response.context)
            self.assertEqual(list(response.context['videos']), [self.vod])
    
    def test_clips_view(self):
        """Tester la vue des clips."""
        # Simuler la réponse de l'API Twitch
        with patch('rastaaslan_app.twitch_utils.fetch_and_update_videos') as mock_fetch:
            mock_fetch.return_value = Video.objects.filter(video_type='Clip')
            
            response = self.client.get(reverse('rastaaslan_app:clips'))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'rastaaslan_app/clips.html')
            self.assertIn('videos', response.context)
            self.assertEqual(list(response.context['videos']), [self.clip])
    
    def test_video_detail_view(self):
        """Tester la vue de détail d'une vidéo."""
        response = self.client.get(reverse('rastaaslan_app:video_detail', args=[self.vod.video_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rastaaslan_app/video_detail.html')
        self.assertEqual(response.context['video'], self.vod)
        self.assertIn('related_videos', response.context)
    
    def test_404_for_nonexistent_video(self):
        """Tester qu'une 404 est renvoyée pour une vidéo inexistante."""
        response = self.client.get(reverse('rastaaslan_app:video_detail', args=['nonexistent_id']))
        self.assertEqual(response.status_code, 404)


class ForumTests(TestCase):
    """Tests pour les fonctionnalités du forum."""
    
    def setUp(self):
        """Configurer les données de test pour le forum."""
        # Créer un utilisateur
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com',
            password='testpassword'
        )
        
        # Créer une catégorie
        self.category = ForumCategory.objects.create(
            name="Test Category",
            slug="test-category",
            description="Une catégorie de test"
        )
        
        # Créer un sujet
        self.topic = ForumTopic.objects.create(
            title="Test Topic",
            slug="test-topic",
            category=self.category,
            author=self.user,
            content="Contenu du sujet de test"
        )
        
        # Créer le premier message du sujet
        self.post = ForumPost.objects.create(
            topic=self.topic,
            author=self.user,
            content="Premier message du sujet de test"
        )
        
        # Client authentifié
        self.client = Client()
    
    def test_forum_home_view(self):
        """Tester la page d'accueil du forum."""
        response = self.client.get(reverse('rastaaslan_app:forum_home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rastaaslan_app/forum/forum_home.html')
        self.assertIn('categories', response.context)
        self.assertIn('stats', response.context)
        
        # Vérifier que notre catégorie est dans le contexte
        categories = list(response.context['categories'])
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0], self.category)
    
    def test_forum_category_view(self):
        """Tester la vue d'une catégorie du forum."""
        response = self.client.get(reverse('rastaaslan_app:forum_category', args=[self.category.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rastaaslan_app/forum/forum_category.html')
        self.assertEqual(response.context['category'], self.category)
        self.assertIn('topics', response.context)
        
        # Vérifier que notre sujet est dans le contexte
        topics = list(response.context['topics'])
        self.assertEqual(len(topics), 1)
        self.assertEqual(topics[0], self.topic)
    
    def test_forum_topic_view(self):
        """Tester la vue d'un sujet du forum."""
        response = self.client.get(reverse('rastaaslan_app:forum_topic', args=[self.category.slug, self.topic.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rastaaslan_app/forum/forum_topic.html')
        self.assertEqual(response.context['topic'], self.topic)
        self.assertIn('posts', response.context)
        
        # Vérifier que le compteur de vues a été incrémenté
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.views_count, 1)
    
    def test_create_topic_requires_login(self):
        """Tester que la création de sujet nécessite d'être connecté."""
        # Tentative sans connexion
        response = self.client.get(reverse('rastaaslan_app:create_topic'))
        self.assertNotEqual(response.status_code, 200)  # Redirection ou 403
        
        # Connexion
        self.client.login(username='testuser', password='testpassword')
        
        # Tentative après connexion
        response = self.client.get(reverse('rastaaslan_app:create_topic'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rastaaslan_app/forum/create_topic.html')
    
    def test_create_topic_post(self):
        """Tester la création d'un sujet via POST."""
        # Connexion
        self.client.login(username='testuser', password='testpassword')
        
        # Données du formulaire
        form_data = {
            'title': 'Nouveau sujet de test',
            'category': self.category.id,
            'content': 'Contenu du nouveau sujet de test'
        }
        
        # Soumission du formulaire
        response = self.client.post(reverse('rastaaslan_app:create_topic'), form_data, follow=True)
        
        # Vérifier la redirection
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que le sujet a été créé
        self.assertTrue(ForumTopic.objects.filter(title='Nouveau sujet de test').exists())
        
        # Vérifier que le premier message a été créé
        new_topic = ForumTopic.objects.get(title='Nouveau sujet de test')
        self.assertTrue(ForumPost.objects.filter(topic=new_topic).exists())