from django.contrib import admin
from .models import Video, UserProfile, ForumCategory, ForumTopic, ForumPost

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

admin.site.register(Video, VideoAdmin)

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
    
    def get_queryset(self, request):
        """Optimiser les requêtes"""
        return super().get_queryset(request).select_related('user')

admin.site.register(UserProfile, UserProfileAdmin)

class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'get_topic_count', 'created_at')
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
        return obj.get_topic_count()
    get_topic_count.short_description = "Nombre de sujets"

admin.site.register(ForumCategory, ForumCategoryAdmin)

class ForumPostInline(admin.TabularInline):
    model = ForumPost
    extra = 0
    fields = ('author', 'content', 'created_at', 'is_edited')
    readonly_fields = ('created_at', 'is_edited')
    can_delete = True
    
    def get_queryset(self, request):
        """Limiter le nombre de messages affichés en ligne"""
        return super().get_queryset(request).select_related('author')[:10]

class ForumTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'created_at', 'is_pinned', 'is_locked', 'views_count', 'get_post_count')
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
    
    def get_queryset(self, request):
        """Optimiser les requêtes"""
        return super().get_queryset(request).select_related('author', 'category')
    
    def get_post_count(self, obj):
        return obj.get_post_count()
    get_post_count.short_description = "Nombre de messages"
    
    # Actions personnalisées
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

admin.site.register(ForumTopic, ForumTopicAdmin)

class ForumPostAdmin(admin.ModelAdmin):
    list_display = ('topic', 'author', 'is_first_post', 'created_at', 'is_edited')
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
    
    def get_queryset(self, request):
        """Optimiser les requêtes"""
        return super().get_queryset(request).select_related('author', 'topic')
    
    def is_first_post(self, obj):
        return obj.is_first_post
    is_first_post.short_description = "Post initial"
    is_first_post.boolean = True

admin.site.register(ForumPost, ForumPostAdmin)