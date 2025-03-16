from django.contrib import admin
from .models import Video, UserProfile, ForumCategory, ForumTopic, ForumPost

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'video_type', 'video_id', 'created_at')
    list_filter = ('video_type', 'created_at')
    search_fields = ('title', 'video_id')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'video_type', 'video_id')
        }),
        ('URLs', {
            'fields': ('url', 'thumbnail_url'),
            'classes': ('collapse',),
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Rendre video_id en lecture seule lors de l'édition mais pas à la création"""
        if obj:  # Si l'objet existe déjà (édition)
            return ('video_id', 'created_at')
        return ('created_at',)  # Sinon (création)
    
    def has_delete_permission(self, request, obj=None):
        # Optionnel : restreindre la suppression par critères
        return True


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'twitch_username', 'is_streamer', 'date_joined')
    list_filter = ('is_streamer', 'date_joined')
    search_fields = ('user__username', 'user__email', 'twitch_username', 'bio')
    readonly_fields = ('date_joined',)
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Informations du profil', {
            'fields': ('avatar', 'bio', 'twitch_username', 'is_streamer')
        }),
        ('Métadonnées', {
            'fields': ('date_joined',),
            'classes': ('collapse',),
        }),
    )


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'created_at')
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


class ForumPostInline(admin.TabularInline):
    model = ForumPost
    extra = 0
    fields = ('author', 'content', 'created_at', 'is_edited')
    readonly_fields = ('created_at', 'is_edited')


@admin.register(ForumTopic)
class ForumTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'created_at', 'is_pinned', 'is_locked', 'views_count')
    list_filter = ('category', 'is_pinned', 'is_locked', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    
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


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ('topic', 'author', 'created_at', 'is_edited')
    list_filter = ('is_edited', 'created_at')
    search_fields = ('content', 'author__username', 'topic__title')
    
    fieldsets = (
        ('Informations du message', {
            'fields': ('topic', 'author', 'content')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at', 'is_edited'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'is_edited')