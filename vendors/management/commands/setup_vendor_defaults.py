from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from vendors.models import Vendor, VendorKYC

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup default vendor data for testing'

    def handle(self, *args, **options):
        # Create test vendor user if doesn't exist
        vendor_email = 'vendor@test.com'
        if not User.objects.filter(email=vendor_email).exists():
            vendor_user = User.objects.create_user(
                username='testvendor',
                email=vendor_email,
                password='testpass123',
                full_name='Test Vendor',
                is_verified=True
            )
            
            # Create vendor profile
            vendor = Vendor.objects.create(
                user=vendor_user,
                store_name='Test Scrap Store',
                business_email=vendor_email,
                business_phone='+91-9876543210',
                store_description='A test scrap store for demo purposes',
                store_address={
                    'street': '123 Test Street',
                    'city': 'Test City',
                    'state': 'Test State',
                    'pincode': '123456'
                },
                kyc_status='approved'
            )
            
            # Create KYC documents
            VendorKYC.objects.create(
                vendor=vendor,
                bank_account_number='1234567890',
                bank_ifsc='TEST0001234',
                bank_account_holder='Test Vendor',
                verification_status='verified'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created test vendor: {vendor.store_name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Test vendor already exists')
            )
