from django import template
from django.utils.safestring import mark_safe
from advertisements.models import Advertisement

register = template.Library()


@register.simple_tag
def show_banner_ads():
    """Display banner advertisements"""
    ads = Advertisement.objects.filter(
        status='active',
        placement='banner'
    )[:3]
    
    if not ads:
        return ''
    
    html = '<div class="row mb-3">'
    for ad in ads:
        html += f'''
        <div class="col-md-4 mb-2">
            <div class="card border-0">
                <a href="{ad.link}" target="_blank" onclick="trackClick('{ad.id}')">
                    <img src="{ad.image.url}" class="card-img-top" alt="{ad.title}" 
                         style="height: 120px; object-fit: cover;">
                </a>
            </div>
        </div>
        '''
    html += '</div>'
    
    return mark_safe(html)


@register.simple_tag
def show_sidebar_ads():
    """Display sidebar advertisements"""
    ads = Advertisement.objects.filter(
        status='active',
        placement='sidebar'
    )[:2]
    
    if not ads:
        return ''
    
    html = ''
    for ad in ads:
        html += f'''
        <div class="card mb-3">
            <a href="{ad.link}" target="_blank" onclick="trackClick('{ad.id}')">
                <img src="{ad.image.url}" class="card-img-top" alt="{ad.title}"
                     style="height: 150px; object-fit: cover;">
            </a>
            <div class="card-body p-2">
                <small class="text-muted">{ad.title}</small>
            </div>
        </div>
        '''
    
    return mark_safe(html)


@register.simple_tag
def ad_tracking_script():
    """Advertisement tracking JavaScript"""
    return mark_safe('''
    <script>
    function trackClick(adId) {
        fetch('/ads/track-click/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ad_id: adId})
        }).catch(error => console.log('Ad tracking error:', error));
    }
    
    // Track ad impressions
    document.addEventListener('DOMContentLoaded', function() {
        const ads = document.querySelectorAll('[data-ad-id]');
        ads.forEach(ad => {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        fetch('/ads/track-impression/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                            },
                            body: JSON.stringify({ad_id: ad.dataset.adId})
                        }).catch(error => console.log('Ad tracking error:', error));
                        observer.unobserve(entry.target);
                    }
                });
            });
            observer.observe(ad);
        });
    });
    </script>
    ''')
