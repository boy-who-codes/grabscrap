from django.core.management.base import BaseCommand
from products.models import Category

class Command(BaseCommand):
    help = 'Adds default scrap metal categories to the database'

    def handle(self, *args, **options):
        categories = [
            {
                'name': 'Iron',
                'description': 'Iron scrap including cast iron, wrought iron, and steel',
                'commission_rate': 5.0,
                'sort_order': 1,
                'is_active': True
            },
            {
                'name': 'Copper',
                'description': 'Copper wire, pipes, and other copper items',
                'commission_rate': 7.5,
                'sort_order': 2,
                'is_active': True
            },
            {
                'name': 'Nickel',
                'description': 'Nickel-based alloys and pure nickel items',
                'commission_rate': 8.0,
                'sort_order': 3,
                'is_active': True
            },
            {
                'name': 'Aluminum',
                'description': 'Aluminum cans, sheets, and other aluminum items',
                'commission_rate': 6.0,
                'sort_order': 4,
                'is_active': True
            },
            {
                'name': 'Brass',
                'description': 'Brass fixtures, fittings, and other brass items',
                'commission_rate': 7.0,
                'sort_order': 5,
                'is_active': True
            },
            {
                'name': 'Stainless Steel',
                'description': 'Stainless steel appliances, cutlery, and other items',
                'commission_rate': 5.5,
                'sort_order': 6,
                'is_active': True
            },
            {
                'name': 'Lead',
                'description': 'Lead pipes, sheets, and other lead items',
                'commission_rate': 6.5,
                'sort_order': 7,
                'is_active': True
            },
            {
                'name': 'Zinc',
                'description': 'Zinc sheets, die-cast parts, and other zinc items',
                'commission_rate': 6.0,
                'sort_order': 8,
                'is_active': True
            },
            {
                'name': 'E-Waste',
                'description': 'Electronic waste including computers, phones, and other devices',
                'commission_rate': 10.0,
                'sort_order': 9,
                'is_active': True
            },
            {
                'name': 'Paper',
                'description': 'Cardboard, newspapers, magazines, and other paper products',
                'commission_rate': 3.0,
                'sort_order': 10,
                'is_active': True
            },
            {
                'name': 'Plastic',
                'description': 'Plastic bottles, containers, and other plastic items',
                'commission_rate': 4.0,
                'sort_order': 11,
                'is_active': True
            }
        ]

        for category_data in categories:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'description': category_data['description'],
                    'commission_rate': category_data['commission_rate'],
                    'sort_order': category_data['sort_order'],
                    'is_active': category_data['is_active']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created category: {category.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Category already exists: {category.name}'))

        self.stdout.write(self.style.SUCCESS('Finished adding categories'))
