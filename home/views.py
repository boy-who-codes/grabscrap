from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView
from django.db import models
from django.db.models import Count, Q
from products.models import Category, Product
from django.views.generic.edit import FormMixin
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

class HomeView(FormMixin, TemplateView):
    template_name = 'home/index.html'
    form_class = None  # We'll handle form in get_context_data
    
    def get_queryset(self):
        # Get all active categories with product counts
        return Category.objects.filter(
            is_active=True
        ).annotate(
            product_count=models.Count('products', filter=Q(products__is_active=True))
        ).filter(
            product_count__gt=0
        ).order_by('sort_order', 'name')
    
    def get_popular_categories(self, queryset):
        # Get top 6 categories by product count
        return queryset.order_by('-product_count')[:6]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = self.get_queryset()
        popular_categories = self.get_popular_categories(categories)
        
        context.update({
            'categories': categories,
            'popular_categories': popular_categories,
            'search_query': self.request.GET.get('q', ''),
            'selected_category': self.request.GET.get('category', '')
        })
        return context

def home(request):
    """Legacy home view - redirects to the root URL"""
    return redirect('root')
