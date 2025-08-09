from django.urls import path
from . import views

app_name = 'kyc_management'

# Admin URLs
admin_urls = [
    path('dashboard/', views.kyc_dashboard, name='dashboard'),
    path('pending/', views.pending_kyc_list, name='pending_list'),
    path('detail/<uuid:vendor_id>/', views.kyc_detail, name='kyc_detail'),
    path('approve-ajax/', views.approve_kyc_ajax, name='approve_ajax'),
]

# Vendor URLs
vendor_urls = [
    path('submit/', views.kyc_submit, name='submit'),
    path('status/', views.kyc_status, name='status'),
    path('reapply/', views.reapply_kyc, name='reapply'),
]

urlpatterns = admin_urls + vendor_urls