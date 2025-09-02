from django.core.management.base import BaseCommand
from core.models import SystemSettings, Category


class Command(BaseCommand):
    help = 'Setup default system settings and categories'

    def handle(self, *args, **options):
        # Default system settings
        defaults = [
            ('SEARCH_RADIUS_KM', '250', 'Default search radius in kilometers'),
            ('ESCROW_MODE', 'auto', 'Escrow release mode: auto or manual'),
            ('GLOBAL_COMMISSION_RATE', '5.0', 'Global commission rate percentage'),
            ('MIN_WALLET_RECHARGE', '100', 'Minimum wallet recharge amount'),
            ('MAX_WALLET_RECHARGE', '50000', 'Maximum wallet recharge amount'),
            ('PLATFORM_NAME', 'KABAADWALA™', 'Platform display name'),
        ]
        
        for key, value, description in defaults:
            setting, created = SystemSettings.objects.get_or_create(
                key=key,
                defaults={'value': value, 'description': description}
            )
            if created:
                self.stdout.write(f'Created setting: {key}')
        
        # Default categories
        categories = [
            'Metal Scrap',
            'Paper & Cardboard',
            'Plastic Waste',
            'Electronic Waste',
            'Glass & Bottles',
            'Textile Waste',
            'Rubber & Tires',
            'Construction Waste',
        ]
        
        for cat_name in categories:
            category, created = Category.objects.get_or_create(
                name=cat_name,
                defaults={'is_active': True}
            )
            if created:
                self.stdout.write(f'Created category: {cat_name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully setup default settings and categories')
        )
