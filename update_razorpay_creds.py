#!/usr/bin/env python3
"""
Script to read Razorpay credentials from rzp.csv and update .env file
"""
import csv
import os

def update_razorpay_credentials():
    # Read credentials from CSV
    try:
        with open('rzp.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            creds = next(reader)
            key_id = creds['key_id']
            key_secret = creds['key_secret']
            
        print(f"✅ Read credentials from rzp.csv:")
        print(f"   Key ID: {key_id}")
        print(f"   Key Secret: {key_secret[:10]}...")
        
        # Read current .env file
        env_lines = []
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                env_lines = f.readlines()
        
        # Update or add Razorpay credentials
        updated_lines = []
        key_id_updated = False
        key_secret_updated = False
        
        for line in env_lines:
            if line.startswith('RAZORPAY_KEY_ID='):
                updated_lines.append(f'RAZORPAY_KEY_ID={key_id}\n')
                key_id_updated = True
            elif line.startswith('RAZORPAY_KEY_SECRET='):
                updated_lines.append(f'RAZORPAY_KEY_SECRET={key_secret}\n')
                key_secret_updated = True
            else:
                updated_lines.append(line)
        
        # Add credentials if not found
        if not key_id_updated:
            updated_lines.append(f'RAZORPAY_KEY_ID={key_id}\n')
        if not key_secret_updated:
            updated_lines.append(f'RAZORPAY_KEY_SECRET={key_secret}\n')
        
        # Write updated .env file
        with open('.env', 'w') as f:
            f.writelines(updated_lines)
        
        print("✅ Updated .env file with Razorpay credentials")
        
    except FileNotFoundError:
        print("❌ rzp.csv file not found")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_razorpay_credentials()
