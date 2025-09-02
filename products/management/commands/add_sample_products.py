from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Category
from vendors.models import Vendor
from products.models import Product
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Add sample products and categories'

    def handle(self, *args, **options):
        # Create categories
        categories_data = [
            {'name': 'Metal Scrap', 'description': 'All types of metal scraps including iron, steel, aluminum'},
            {'name': 'Paper Scrap', 'description': 'Newspapers, cardboard, office papers'},
            {'name': 'Plastic Scrap', 'description': 'PET bottles, plastic containers, bags'},
            {'name': 'Electronic Scrap', 'description': 'Old electronics, circuit boards, cables'},
            {'name': 'Glass Scrap', 'description': 'Bottles, window glass, mirrors'},
            {'name': 'Textile Scrap', 'description': 'Old clothes, fabric waste, cotton'},
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'is_active': True,
                    'commission_rate': 5.0
                }
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Ensure we have a vendor
        vendor_user, created = User.objects.get_or_create(
            email='vendor@test.com',
            defaults={
                'username': 'testvendor',
                'full_name': 'Test Vendor',
                'user_type': 'vendor',
                'is_verified': True
            }
        )
        
        vendor, created = Vendor.objects.get_or_create(
            user=vendor_user,
            defaults={
                'store_name': 'Test Scrap Store',
                'business_email': 'vendor@test.com',
                'business_phone': '+91-9876543210',
                'store_description': 'Premium quality scrap materials',
                'store_address': {
                    'street': '123 Test Street',
                    'city': 'Test City',
                    'state': 'Test State',
                    'pincode': '123456'
                },
                'kyc_status': 'approved'
            }
        )
        
        # Sample products data
        products_data = [
            # Metal Scrap
            {'title': 'Iron Scrap - Mixed Grade', 'category': 'Metal Scrap', 'price': 25.50, 'unit': 'kg', 'description': 'High quality mixed iron scrap suitable for recycling'},
            {'title': 'Aluminum Cans', 'category': 'Metal Scrap', 'price': 85.00, 'unit': 'kg', 'description': 'Clean aluminum beverage cans, sorted and compressed'},
            {'title': 'Copper Wire Scrap', 'category': 'Metal Scrap', 'price': 650.00, 'unit': 'kg', 'description': 'Pure copper wire scrap, insulation removed'},
            {'title': 'Stainless Steel Scrap', 'category': 'Metal Scrap', 'price': 120.00, 'unit': 'kg', 'description': 'Grade 304 stainless steel scrap pieces'},
            
            # Paper Scrap
            {'title': 'Old Newspapers', 'category': 'Paper Scrap', 'price': 12.00, 'unit': 'kg', 'description': 'Clean old newspapers, sorted and bundled'},
            {'title': 'Cardboard Boxes', 'category': 'Paper Scrap', 'price': 8.50, 'unit': 'kg', 'description': 'Corrugated cardboard boxes, flattened'},
            {'title': 'Office Paper Waste', 'category': 'Paper Scrap', 'price': 15.00, 'unit': 'kg', 'description': 'White office paper, A4 size, clean'},
            {'title': 'Mixed Paper Scrap', 'category': 'Paper Scrap', 'price': 10.00, 'unit': 'kg', 'description': 'Mixed paper waste, magazines, books'},
            
            # Plastic Scrap
            {'title': 'PET Bottles', 'category': 'Plastic Scrap', 'price': 18.00, 'unit': 'kg', 'description': 'Clear PET bottles, labels removed, crushed'},
            {'title': 'HDPE Containers', 'category': 'Plastic Scrap', 'price': 22.00, 'unit': 'kg', 'description': 'High-density polyethylene containers, clean'},
            {'title': 'Plastic Bags', 'category': 'Plastic Scrap', 'price': 14.00, 'unit': 'kg', 'description': 'Mixed plastic bags, sorted by color'},
            {'title': 'PP Containers', 'category': 'Plastic Scrap', 'price': 20.00, 'unit': 'kg', 'description': 'Polypropylene containers and lids'},
            
            # Electronic Scrap
            {'title': 'Computer Motherboards', 'category': 'Electronic Scrap', 'price': 450.00, 'unit': 'piece', 'description': 'Old computer motherboards with components'},
            {'title': 'Mobile Phone Scrap', 'category': 'Electronic Scrap', 'price': 150.00, 'unit': 'piece', 'description': 'Non-working mobile phones for parts'},
            {'title': 'Electronic Cables', 'category': 'Electronic Scrap', 'price': 35.00, 'unit': 'kg', 'description': 'Mixed electronic cables and wires'},
            {'title': 'CRT Monitor Scrap', 'category': 'Electronic Scrap', 'price': 80.00, 'unit': 'piece', 'description': 'Old CRT monitors for recycling'},
            
            # Glass Scrap
            {'title': 'Glass Bottles - Clear', 'category': 'Glass Scrap', 'price': 6.00, 'unit': 'kg', 'description': 'Clear glass bottles, sorted and clean'},
            {'title': 'Glass Bottles - Colored', 'category': 'Glass Scrap', 'price': 4.50, 'unit': 'kg', 'description': 'Colored glass bottles, mixed colors'},
            {'title': 'Window Glass Scrap', 'category': 'Glass Scrap', 'price': 8.00, 'unit': 'kg', 'description': 'Flat window glass pieces, clean'},
            
            # Textile Scrap
            {'title': 'Cotton Fabric Waste', 'category': 'Textile Scrap', 'price': 12.00, 'unit': 'kg', 'description': 'Pure cotton fabric scraps, sorted'},
            {'title': 'Mixed Clothing', 'category': 'Textile Scrap', 'price': 8.00, 'unit': 'kg', 'description': 'Used clothing in good condition'},
            {'title': 'Denim Scraps', 'category': 'Textile Scrap', 'price': 15.00, 'unit': 'kg', 'description': 'Denim fabric scraps, various colors'},
        ]
        
        # Create products
        created_count = 0
        for product_data in products_data:
            category = Category.objects.get(name=product_data['category'])
            
            product, created = Product.objects.get_or_create(
                title=product_data['title'],
                vendor=vendor,
                defaults={
                    'category': category,
                    'description': product_data['description'],
                    'price': product_data['price'],
                    'unit': product_data['unit'],
                    'stock_quantity': random.randint(50, 500),
                    'minimum_order_quantity': 1,
                    'is_active': True,
                    'is_featured': random.choice([True, False]),
                    'tags': ['scrap', 'recycling', category.name.lower().replace(' ', '-')],
                    'specifications': {
                        'condition': 'Used',
                        'quality': random.choice(['Good', 'Excellent', 'Fair']),
                        'origin': 'Local Collection'
                    }
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Created product: {product.title}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(categories)} categories and {created_count} products'
            )
        )
