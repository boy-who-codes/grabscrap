from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from home.views import HomeView

class RootView(HomeView):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user = request.user
            if user.is_superuser:
                return redirect('accounts:admin_dashboard')
            elif user.user_type == 'vendor':
                return redirect('vendor_dashboard')
            else:
                return redirect('user_dashboard')
        return super().get(request, *args, **kwargs)

urlpatterns = [
    path('', RootView.as_view(), name='root'),
    path('admin/', admin.site.urls),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('dashboard/', include('dashboard.urls')),
    path('kyc/', include('kyc_management.urls')),
    path('products/', include('products.urls')),
    path('orders/', include('orders.urls')),
    path('wallet/', include('wallet.urls')),
    path('chat/', include('chat.urls')),
    path('home/', include(('home.urls', 'home'), namespace='home')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)