from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser
from .models import Payment

class PaymentRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_paths = [
            '/',  # Login page
            '/register/',
            '/logout/',
            '/payment/',
            '/payment/success/',
            '/payment/failure/',
            '/admin/',
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        # Allow all users to access exempt paths (login, register, logout, payment, admin)
        if any(request.path.startswith(path) for path in self.exempt_paths):
            response = self.get_response(request)
            return response
        
        # Only check payment for authenticated users accessing protected content
        if request.user.is_authenticated and not isinstance(request.user, AnonymousUser):
            # Check if user has active payment
            has_active_payment = Payment.objects.filter(
                user=request.user,
                status='completed'
            ).exists()
            
            # Redirect to payment if no active payment
            if not has_active_payment:
                return redirect('/payment/')
        
        response = self.get_response(request)
        return response