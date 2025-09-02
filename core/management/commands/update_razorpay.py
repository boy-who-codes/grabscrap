from django.core.management.base import BaseCommand
import csv
import os

class Command(BaseCommand):
    help = 'Update Razorpay credentials from rzp.csv to .env file'

    def handle(self, *args, **options):
        try:
            # Read credentials from CSV
            with open('rzp.csv', 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                creds = next(reader)
                key_id = creds['key_id']
                key_secret = creds['key_secret']
            
            self.stdout.write(f"✅ Read credentials from rzp.csv:")
            self.stdout.write(f"   Key ID: {key_id}")
            self.stdout.write(f"   Key Secret: {key_secret[:10]}...")
            
            # Update environment variables
            os.environ['RAZORPAY_KEY_ID'] = key_id
            os.environ['RAZORPAY_KEY_SECRET'] = key_secret
            
            self.stdout.write(
                self.style.SUCCESS('✅ Razorpay credentials updated successfully!')
            )
            
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR('❌ rzp.csv file not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {e}')
            )
