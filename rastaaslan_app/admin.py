from django.contrib import admin
from .models import Video

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