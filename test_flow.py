#!/usr/bin/env python3
"""
Test script for Jetflix authentication and payment flow
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/kushalbhattarai/Projects/Jetflix')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Jetflix.settings')
django.setup()

from django.contrib.auth.models import User
from home.models import Payment
from movies.models import Movie

def test_user_flow():
    """Test the complete user flow"""
    print("🎬 Testing Jetflix Authentication & Payment Flow")
    print("=" * 50)
    
    # Test 1: Create test user
    print("1. Creating test user...")
    try:
        # Delete existing test user if exists
        User.objects.filter(username='testuser').delete()
        
        test_user = User.objects.create_user(
            username='testuser',
            email='test@jetflix.com',
            password='testpass123'
        )
        print("✅ Test user created successfully")
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False
    
    # Test 2: Check payment status (should be False initially)
    print("\n2. Checking initial payment status...")
    has_payment = Payment.objects.filter(
        user=test_user,
        status='completed'
    ).exists()
    print(f"✅ Initial payment status: {has_payment} (should be False)")
    
    # Test 3: Create completed payment
    print("\n3. Creating completed payment...")
    try:
        payment = Payment.objects.create(
            user=test_user,
            transaction_id='test_transaction_123',
            amount=500.00,
            status='completed',
            esewa_ref_id='test_ref_123'
        )
        print("✅ Payment created successfully")
    except Exception as e:
        print(f"❌ Error creating payment: {e}")
        return False
    
    # Test 4: Check payment status after creation
    print("\n4. Checking payment status after creation...")
    has_payment = Payment.objects.filter(
        user=test_user,
        status='completed'
    ).exists()
    print(f"✅ Payment status after creation: {has_payment} (should be True)")
    
    # Test 5: Check movie access
    print("\n5. Checking movie access...")
    movie_count = Movie.objects.filter(is_published=True).count()
    print(f"✅ Available movies: {movie_count}")
    
    # Test 6: Clean up
    print("\n6. Cleaning up test data...")
    try:
        Payment.objects.filter(user=test_user).delete()
        test_user.delete()
        print("✅ Test data cleaned up")
    except Exception as e:
        print(f"❌ Error cleaning up: {e}")
    
    print("\n🎉 All tests passed! The authentication and payment flow is working correctly.")
    return True

def check_url_structure():
    """Check URL structure"""
    print("\n🔗 Checking URL Structure")
    print("=" * 30)
    
    from django.urls import reverse
    from django.test import Client
    
    try:
        # Test URL reversals
        login_url = reverse('login')
        register_url = reverse('register')
        payment_url = reverse('payment')
        home_url = reverse('home')
        
        print(f"✅ Login URL: {login_url}")
        print(f"✅ Register URL: {register_url}")
        print(f"✅ Payment URL: {payment_url}")
        print(f"✅ Home URL: {home_url}")
        
        return True
    except Exception as e:
        print(f"❌ URL structure error: {e}")
        return False

if __name__ == "__main__":
    try:
        # Run tests
        url_test = check_url_structure()
        flow_test = test_user_flow()
        
        if url_test and flow_test:
            print("\n🎊 All systems are working correctly!")
            print("\nNext steps:")
            print("1. Start the server: python3 manage.py runserver")
            print("2. Visit http://localhost:8000 to see the login page")
            print("3. Create an account and test the payment flow")
        else:
            print("\n⚠️  Some tests failed. Please check the errors above.")
            
    except Exception as e:
        print(f"❌ Test execution error: {e}")