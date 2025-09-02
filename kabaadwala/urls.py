from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Core app (home page)
    path('', include('core.urls')),
    
    # App-specific URLs
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('wallet/', include('wallet.urls')),
    path('orders/', include('orders.urls')),
    path('vendors/', include('vendors.urls')),
    path('chat/', include('chat.urls')),
    path('ads/', include('advertisements.urls')),
    path('coupons/', include('coupons.urls')),
    path('admin-panel/', include('custom_admin.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
