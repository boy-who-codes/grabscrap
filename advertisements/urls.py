from django.urls import path
from . import views

app_name = 'advertisements'

urlpatterns = [
    path('track-impression/', views.track_impression, name='track_impression'),
    path('click/<uuid:ad_id>/', views.track_click, name='track_click'),
]
