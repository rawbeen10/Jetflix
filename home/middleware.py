from django.shortcuts import redirect
from django.contrib.auth.models import AnonymousUser
from .models import Payment

class PaymentRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_paths = [
            '/',
            '/register/',
            '/logout/',
            '/admin/',
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        if any(request.path.startswith(path) for path in self.exempt_paths):
            return self.get_response(request)

        if request.user.is_authenticated and not isinstance(request.user, AnonymousUser):
            has_active_payment = Payment.objects.filter(
                user=request.user,
                status='completed'
            ).exists()

            if not has_active_payment:
                return redirect('/payment/')

        return self.get_response(request)
