from django.shortcuts import redirect
from django.contrib.auth.models import AnonymousUser
from .models import Payment


class PaymentRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        # These paths are always allowed through — no login or payment check
        self.exempt_prefixes = [
            '/',              # login page (exact match handled below)
            '/login/',
            '/register/',
            '/logout/',
            '/payment/',      # covers /payment/, /payment/success/, /payment/failure/
            '/admin/',
            '/adminpanel/',
            '/static/',
            '/media/',
            '/verify-payment/',
        ]

    def _is_exempt(self, path):
        if path == '/':
            return True
        for prefix in self.exempt_prefixes:
            if path.startswith(prefix):
                return True
        return False

    def __call__(self, request):
        # Always allow exempt paths
        if self._is_exempt(request.path):
            return self.get_response(request)

        # Unauthenticated users — send to login
        if not request.user.is_authenticated or isinstance(request.user, AnonymousUser):
            return redirect('/')

        # Authenticated but no completed payment — send to payment page
        has_payment = Payment.objects.filter(
            user=request.user,
            status='completed'
        ).exists()

        if not has_payment:
            return redirect('/payment/')

        return self.get_response(request)
