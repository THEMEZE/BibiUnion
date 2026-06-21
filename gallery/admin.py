from django.contrib import admin
from .models import Photo


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'auteur', 'table', 'date_upload', 'thumbnail_preview')
    list_filter = ('table', 'date_upload')
    search_fields = ('auteur',)
    readonly_fields = ('thumbnail_preview', 'date_upload')

    def thumbnail_preview(self, obj):
        from django.utils.html import format_html
        if obj.thumbnail:
            return format_html('<img src="{}" style="max-height: 80px;" />', obj.thumbnail.url)
        return "(pas de miniature)"
    thumbnail_preview.short_description = "Aperçu"
