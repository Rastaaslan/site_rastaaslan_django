"""
rastaaslan_app/admin.py
Enhanced admin interface for the Rastaaslan website
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Video, UserProfile, ForumCategory, ForumTopic, 
    ForumPost, UserTopicView, PostReaction
)

# Admin site customization
admin.site.site_header = 'Administration Rastaaslan'
admin.site.site_title = 'Administration Rastaaslan'
admin.site.index_title = 'Gestion du site'

# Mixins for common functionality
class LinkToRelatedMixin:
    """Mixin to add links to related objects"""
    
    def get_link_to_obj(self, url_name, obj_id, label):
        """Generate a link to a related object"""
        if not obj_id:
            return '—'
        url = reverse(url_name, args=[obj_id])
        return format_html('<a href="{}">{}</a>', url, label)

class OptimizedQuerysetMixin:
    """Mixin for optimized admin queries"""
    
    def get_queryset(self, request):
        """Optimize querysets with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        if hasattr(self, 'select_related_fields'):
            qs = qs.select_related(*self.select_related_fields)
        if hasattr(self, 'prefetch_related_fields'):
            qs = qs.prefetch_related(*self.prefetch_related_fields)
        return qs

# Video Management
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'video_type', 'video_id', 'created_at', 'thumbnail_preview')
    list_filter = ('video_type', 'created_at')
    search_fields = ('title', 'video_id')
    readonly_fields = ('created_at', 'thumbnail_preview')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'video_type', 'video_id', 'thumbnail_preview')
        }),
        ('URLs', {
            'fields': ('url', 'thumbnail_url'),
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    list_per_page = 20
    
    def get_readonly_fields(self, request, obj=None):
        """Make video_id read-only when editing but not when creating"""
        if obj:  # If object exists (editing)
            return ('video_id', 'created_at', 'thumbnail_preview')
        return ('created_at', 'thumbnail_preview')
    
    def thumbnail_preview(self, obj):
        """Display thumbnail preview in admin"""
        if obj.thumbnail_url:
            return format_html('<img src="{}" style="max-width: 200px; max-height: 100px;" />', 
                              obj.get_thumbnail_url_formatted())
        return "Pas d'image"
    thumbnail_preview.short_description = "Aperçu"

admin.site.register(Video, VideoAdmin)

# User Management
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'twitch_username', 'is_streamer', 'date_joined', 'activity_level')
    list_filter = ('is_streamer', 'date_joined')
    search_fields = ('user__username', 'user__email', 'twitch_username', 'bio')
    readonly_fields = ('date_joined', 'activity_level', 'avatar_preview')
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Informations du profil', {
            'fields': ('avatar', 'avatar_preview', 'bio', 'twitch_username', 'is_streamer')
        }),
        ('Activité', {
            'fields': ('activity_level',),
        }),
        ('Métadonnées', {
            'fields': ('date_joined',),
            'classes': ('collapse',),
        }),
    )
    
    select_related_fields = ['user']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def activity_level(self, obj):
        """Show user activity level with visual indicator"""
        posts_count = ForumPost.objects.filter(author=obj.user).count()
        topics_count = ForumTopic.objects.filter(author=obj.user).count()
        
        # Calculate activity score (1 point per post, 3 points per topic)
        score = posts_count + (topics_count * 3)
        
        if score == 0:
            return format_html('<span style="color: gray;">Inactif (0 posts)</span>')
        elif score < 10:
            return format_html('<span style="color: #7CB9E8;">Faible ({} posts, {} sujets)</span>', 
                              posts_count, topics_count)
        elif score < 50:
            return format_html('<span style="color: #006400;">Modéré ({} posts, {} sujets)</span>', 
                              posts_count, topics_count)
        else:
            return format_html('<span style="color: #C41E3A; font-weight: bold;">Élevé ({} posts, {} sujets)</span>', 
                             posts_count, topics_count)
    activity_level.short_description = "Niveau d'activité"
    
    def avatar_preview(self, obj):
        """Display avatar preview in admin"""
        if obj.avatar:
            return format_html('<img src="{}" style="max-width: 100px; max-height: 100px; border-radius: 50%;" />', 
                              obj.avatar)
        return format_html('<div style="width: 100px; height: 100px; background-color: #ccc; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 40px;">{}</div>', 
                          obj.user.username[0].upper() if obj.user.username else '?')
    avatar_preview.short_description = "Aperçu de l'avatar"

admin.site.register(UserProfile, UserProfileAdmin)

# Forum Management
class ForumPostInline(admin.TabularInline):
    model = ForumPost
    extra = 0
    fields = ('author', 'content_preview', 'created_at', 'is_edited')
    readonly_fields = ('created_at', 'is_edited', 'content_preview')
    can_delete = True
    show_change_link = True
    verbose_name = "Message"
    verbose_name_plural = "Messages"
    
    def get_queryset(self, request):
        """Limit the number of posts shown inline and optimize queries"""
        return super().get_queryset(request).select_related('author').order_by('-created_at')[:10]
    
    def content_preview(self, obj):
        """Show a preview of the content"""
        if obj.content:
            return obj.content[:150] + ('...' if len(obj.content) > 150 else '')
        return "—"
    content_preview.short_description = "Contenu (aperçu)"

class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'get_topic_count', 'get_post_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Informations de la catégorie', {
            'fields': ('name', 'slug', 'description', 'icon')
        }),
        ('Configuration', {
            'fields': ('order',),
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at',)
    
    def get_topic_count(self, obj):
        return obj.topics.count()
    get_topic_count.short_description = "Nombre de sujets"
    
    def get_post_count(self, obj):
        return ForumPost.objects.filter(topic__category=obj).count()
    get_post_count.short_description = "Nombre de messages"

class PostReactionInline(admin.TabularInline):
    model = PostReaction
    extra = 0
    fields = ('user', 'reaction_type', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = True
    verbose_name = "Réaction"
    verbose_name_plural = "Réactions"
    max_num = 10
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

class ForumTopicAdmin(admin.ModelAdmin, OptimizedQuerysetMixin):
    list_display = ('title', 'category_link', 'author_link', 'created_at', 'is_pinned', 'is_locked', 
                   'views_count', 'get_post_count', 'last_activity')
    list_filter = ('category', 'is_pinned', 'is_locked', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    actions = ['pin_topics', 'unpin_topics', 'lock_topics', 'unlock_topics']
    
    fieldsets = (
        ('Informations du sujet', {
            'fields': ('title', 'slug', 'category', 'author', 'content')
        }),
        ('Configuration', {
            'fields': ('is_pinned', 'is_locked', 'views_count'),
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'views_count')
    inlines = [ForumPostInline]
    
    select_related_fields = ['author', 'category']
    
    def get_post_count(self, obj):
        return obj.posts.count()
    get_post_count.short_description = "Nombre de messages"
    
    def last_activity(self, obj):
        """Display date of last activity with link to latest post"""
        latest_post = obj.posts.order_by('-created_at').first()
        if latest_post:
            time_display = latest_post.created_at.strftime('%d/%m/%Y %H:%M')
            return format_html('{} par <a href="{}">{}</a>', 
                             time_display,
                             reverse('admin:rastaaslan_app_forumpost_change', args=[latest_post.id]),
                             latest_post.author.username if latest_post.author else "—")
        return "—"
    last_activity.short_description = "Dernière activité"
    
    def category_link(self, obj):
        """Display category with link to filter"""
        if obj.category:
            return format_html('<a href="{}?category__id__exact={}">{}</a>',
                            reverse('admin:rastaaslan_app_forumtopic_changelist'),
                            obj.category.id,
                            obj.category.name)
        return "—"
    category_link.short_description = "Catégorie"
    category_link.admin_order_field = 'category__name'
    
    def author_link(self, obj):
        """Display author with link to user admin"""
        if obj.author:
            return format_html('<a href="{}">{}</a>',
                            reverse('admin:auth_user_change', args=[obj.author.id]),
                            obj.author.username)
        return "—"
    author_link.short_description = "Auteur"
    author_link.admin_order_field = 'author__username'
    
    # Custom actions
    def pin_topics(self, request, queryset):
        queryset.update(is_pinned=True)
    pin_topics.short_description = "Épingler les sujets sélectionnés"
    
    def unpin_topics(self, request, queryset):
        queryset.update(is_pinned=False)
    unpin_topics.short_description = "Désépingler les sujets sélectionnés"
    
    def lock_topics(self, request, queryset):
        queryset.update(is_locked=True)
    lock_topics.short_description = "Verrouiller les sujets sélectionnés"
    
    def unlock_topics(self, request, queryset):
        queryset.update(is_locked=False)
    unlock_topics.short_description = "Déverrouiller les sujets sélectionnés"

class ForumPostAdmin(admin.ModelAdmin, OptimizedQuerysetMixin, LinkToRelatedMixin):
    list_display = ('id', 'topic_link', 'author_link', 'is_first_post', 'content_preview', 
                   'created_at', 'is_edited', 'reactions_count')
    list_filter = ('is_edited', 'created_at', 'topic__category')
    search_fields = ('content', 'author__username', 'topic__title')
    
    fieldsets = (
        ('Informations du message', {
            'fields': ('topic', 'author', 'content', 'content_html_preview')
        }),
        ('Mentions et réactions', {
            'fields': ('mentioned_users', 'get_reactions'),
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at', 'is_edited'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'is_edited', 
                      'content_html_preview', 'get_reactions')
    filter_horizontal = ('mentioned_users',)
    inlines = [PostReactionInline]
    
    select_related_fields = ['author', 'topic', 'topic__category']
    list_per_page = 20
    
    def get_reactions(self, obj):
        """Display reactions summary"""
        reactions = obj.reactions.values('reaction_type').annotate(count=Count('id'))
        if not reactions:
            return "Aucune réaction"
        
        reaction_emojis = {
            'like': '👍',
            'thanks': '🙏',
            'funny': '😂',
            'insightful': '💡'
        }
        
        result = []
        for r in reactions:
            emoji = reaction_emojis.get(r['reaction_type'], '')
            result.append(f"{emoji} {r['reaction_type']}: {r['count']}")
        
        return mark_safe('<br>'.join(result))
    get_reactions.short_description = "Réactions"
    
    def reactions_count(self, obj):
        """Count reactions for list display"""
        return obj.reactions.count()
    reactions_count.short_description = "Réactions"
    
    def content_preview(self, obj):
        """Show a preview of the content in list display"""
        if obj.content:
            return obj.content[:100] + ('...' if len(obj.content) > 100 else '')
        return "—"
    content_preview.short_description = "Contenu (aperçu)"
    
    def content_html_preview(self, obj):
        """Show rendered HTML in form view"""
        return format_html('<div style="padding: 10px; background: #f8f9fa; border: 1px solid #ddd; border-radius: 4px;">{}</div>', 
                         obj.content_html)
    content_html_preview.short_description = "Aperçu HTML"
    
    def is_first_post(self, obj):
        """Check if post is the first in its topic"""
        return obj.is_first_post
    is_first_post.short_description = "Post initial"
    is_first_post.boolean = True
    
    def topic_link(self, obj):
        """Link to the topic in admin"""
        if obj.topic:
            return self.get_link_to_obj(
                'admin:rastaaslan_app_forumtopic_change', 
                obj.topic.id, 
                obj.topic.title
            )
        return "—"
    topic_link.short_description = "Sujet"
    topic_link.admin_order_field = 'topic__title'
    
    def author_link(self, obj):
        """Link to the author in admin"""
        if obj.author:
            return self.get_link_to_obj(
                'admin:auth_user_change', 
                obj.author.id, 
                obj.author.username
            )
        return "—"
    author_link.short_description = "Auteur"
    author_link.admin_order_field = 'author__username'

class UserTopicViewAdmin(admin.ModelAdmin, OptimizedQuerysetMixin):
    list_display = ('user', 'topic', 'last_viewed')
    list_filter = ('last_viewed',)
    search_fields = ('user__username', 'topic__title')
    readonly_fields = ('last_viewed',)
    
    select_related_fields = ['user', 'topic', 'topic__category']
    
    def has_add_permission(self, request):
        """Disable adding view records manually"""
        return False

class PostReactionAdmin(admin.ModelAdmin, OptimizedQuerysetMixin):
    list_display = ('id', 'post_link', 'user_link', 'reaction_display', 'created_at')
    list_filter = ('reaction_type', 'created_at')
    search_fields = ('user__username', 'post__content', 'post__topic__title')
    readonly_fields = ('created_at',)
    
    select_related_fields = ['user', 'post', 'post__topic', 'post__author']
    
    def reaction_display(self, obj):
        """Display reaction with emoji"""
        reaction_emojis = {
            'like': '👍',
            'thanks': '🙏',
            'funny': '😂',
            'insightful': '💡'
        }
        emoji = reaction_emojis.get(obj.reaction_type, '')
        return f"{emoji} {obj.get_reaction_type_display()}"
    reaction_display.short_description = "Réaction"
    
    def post_link(self, obj):
        """Link to the post"""
        if obj.post:
            preview = obj.post.content[:30] + ('...' if len(obj.post.content) > 30 else '')
            return format_html('<a href="{}">{}</a>',
                            reverse('admin:rastaaslan_app_forumpost_change', args=[obj.post.id]),
                            preview)
        return "—"
    post_link.short_description = "Message"
    
    def user_link(self, obj):
        """Link to the user"""
        if obj.user:
            return format_html('<a href="{}">{}</a>',
                            reverse('admin:auth_user_change', args=[obj.user.id]),
                            obj.user.username)
        return "—"
    user_link.short_description = "Utilisateur"

# Register all admin models
admin.site.register(ForumCategory, ForumCategoryAdmin)
admin.site.register(ForumTopic, ForumTopicAdmin)
admin.site.register(ForumPost, ForumPostAdmin)
admin.site.register(UserTopicView, UserTopicViewAdmin)
admin.site.register(PostReaction, PostReactionAdmin)

# Custom admin index
class RastaaslanAdminSite(admin.AdminSite):
    """Custom admin site for Rastaaslan"""
    site_header = 'Administration Rastaaslan'
    site_title = 'Administration Rastaaslan'
    index_title = 'Tableau de bord'
    
    def get_app_list(self, request):
        """
        Return a custom app list with models grouped by functional area
        instead of Django app
        """
        app_list = super().get_app_list(request)
        
        # Custom ordering of apps and models
        custom_order = {
            'rastaaslan_app': 1,
            'auth': 2,
            'sites': 3,
            'contenttypes': 4,
            'sessions': 5,
        }
        
        # Custom ordering of models within apps
        model_order = {
            'Video': 1,
            'UserProfile': 2,
            'ForumCategory': 3,
            'ForumTopic': 4,
            'ForumPost': 5,
            'UserTopicView': 6,
            'PostReaction': 7,
            'User': 1,
            'Group': 2,
        }
        
        # Sort apps
        app_list.sort(key=lambda x: custom_order.get(x['app_label'], 99))
        
        # Sort models within each app
        for app in app_list:
            app['models'].sort(key=lambda x: model_order.get(x['object_name'], 99))
        
        return app_list

# Note: To use the custom admin site, you would uncomment the following lines
# and update your urls.py accordingly. This is provided as reference but not
# activated to avoid breaking the existing site setup.

# from django.contrib import admin
# admin.site = RastaaslanAdminSite()
# admin.autodiscover()