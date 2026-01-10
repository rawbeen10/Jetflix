#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/kushalbhattarai/Projects/Jetflix')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Jetflix.settings')
django.setup()

from django.contrib.auth.models import User
from home.models import Payment

def test_payment_system():
    print("Testing Payment System...")
    
    # Create a test user
    try:
        user = User.objects.get(username='testuser')
        print(f"Using existing user: {user.username}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        print(f"Created test user: {user.username}")
    
    # Check if user has payment
    has_payment = Payment.objects.filter(user=user, status='completed').exists()
    print(f"User has active payment: {has_payment}")
    
    # Create a test payment
    if not has_payment:
        payment = Payment.objects.create(
            user=user,
            transaction_id='test_txn_123',
            status='completed',
            esewa_ref_id='test_ref_123'
        )
        print(f"Created test payment: {payment}")
        print(f"Payment is active: {payment.is_active}")
    
    print("Payment system test completed!")

if __name__ == '__main__':
    test_payment_system()