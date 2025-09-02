from django.contrib import admin
from .models import Advertisement, AdClick, AdImpression


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ['title', 'placement', 'status', 'impressions', 'clicks', 'ctr', 'start_date', 'end_date']
    list_filter = ['status', 'placement', 'start_date', 'end_date']
    search_fields = ['title', 'description']
    readonly_fields = ['impressions', 'clicks', 'ctr', 'created_at', 'updated_at']
    
    def ctr(self, obj):
        return f"{obj.ctr:.2f}%"
    ctr.short_description = 'CTR'


@admin.register(AdClick)
class AdClickAdmin(admin.ModelAdmin):
    list_display = ['advertisement', 'user', 'ip_address', 'clicked_at']
    list_filter = ['clicked_at', 'advertisement']
    readonly_fields = ['clicked_at']


@admin.register(AdImpression)
class AdImpressionAdmin(admin.ModelAdmin):
    list_display = ['advertisement', 'user', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at', 'advertisement']
    readonly_fields = ['viewed_at']
