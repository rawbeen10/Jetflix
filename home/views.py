from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from .forms import CustomUserCreationForm
from .models import Payment
from movies.models import Movie, Watchlist, WatchHistory, UserInteraction, Favorite
import logging
import os
import mimetypes
import uuid
import hashlib
import hmac
import base64
import json
import requests

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# eSewa v2 Sandbox Configuration
# -----------------------------------------------------------------------
ESEWA_MERCHANT_CODE  = 'EPAYTEST'
ESEWA_SECRET_KEY     = '8gBm/:&EnhH.1/q'
ESEWA_PAYMENT_URL    = 'https://rc.esewa.com.np/api/epay/main/v2/form'
ESEWA_STATUS_URL     = 'https://rc.esewa.com.np/api/epay/transaction/status/'
SUBSCRIPTION_AMOUNT  = '500'
ESEWA_CLIENT_ID      = 'JB0BBQ4aD0UqIThFJwAKBgAXEUkEGQUBBAwdOgABHD4DChwUAB0R'
ESEWA_CLIENT_SECRET  = 'BhwIWQQADhIYSxILExMcAgFXFhcOBwAKBgAXEQ=='

# For local dev set this to your ngrok URL e.g. 'https://xxxx.ngrok.io'
# Leave None in production — request.build_absolute_uri is used automatically
ESEWA_CALLBACK_BASE  = None
# -----------------------------------------------------------------------


def video_stream(request, path):
    """Serve video files with HTTP Range request support so browsers can seek and get duration."""
    from django.conf import settings
    full_path = os.path.join(settings.MEDIA_ROOT, path)

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        return HttpResponse(status=404)

    file_size = os.path.getsize(full_path)
    content_type, _ = mimetypes.guess_type(full_path)
    content_type = content_type or 'video/mp4'

    range_header = request.META.get('HTTP_RANGE', '').strip()

    if range_header:
        range_match = range_header.replace('bytes=', '').split('-')
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if range_match[1] else file_size - 1
        end = min(end, file_size - 1)
        length = end - start + 1

        def file_iterator(path, start, length, chunk=8192):
            with open(path, 'rb') as f:
                f.seek(start)
                remaining = length
                while remaining > 0:
                    data = f.read(min(chunk, remaining))
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        response = StreamingHttpResponse(
            file_iterator(full_path, start, length),
            status=206,
            content_type=content_type,
        )
        response['Content-Length'] = str(length)
        response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        response['Accept-Ranges'] = 'bytes'
        return response

    # No range header — serve full file
    def full_iterator(path, chunk=8192):
        with open(path, 'rb') as f:
            while True:
                data = f.read(chunk)
                if not data:
                    break
                yield data

    response = StreamingHttpResponse(full_iterator(full_path), content_type=content_type)
    response['Content-Length'] = str(file_size)
    response['Accept-Ranges'] = 'bytes'
    return response


# Home / Register
def register_view(request):
    try:
        if request.method == 'POST':
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                user = form.save()
                login(request, user)
                messages.success(request, "Account created successfully! Please complete payment to access movies.")
                return redirect('payment')
            else:
                return render(request, 'home/register.html', {'form': form})
        else:
            form = CustomUserCreationForm()
        return render(request, 'home/register.html', {'form': form})
    except Exception as e:
        logger.error(f"Error in register_view: {str(e)}")
        messages.error(request, "An error occurred during registration. Please try again.")
        return render(request, 'home/register.html', {'form': CustomUserCreationForm()})


# Login
def login_view(request):
    if request.user.is_authenticated:
        has_payment = Payment.objects.filter(user=request.user, status='completed').exists()
        return redirect('home') if has_payment else redirect('payment')

    try:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                has_payment = Payment.objects.filter(user=user, status='completed').exists()
                if has_payment:
                    messages.success(request, f"Welcome back, {user.username}!")
                    return redirect('home')
                else:
                    return redirect('payment')
            else:
                messages.error(request, "Invalid username or password.")

        return render(request, 'home/login.html')
    except Exception as e:
        logger.error(f"Error in login_view: {str(e)}")
        messages.error(request, "An error occurred during login. Please try again.")
        return render(request, 'home/login.html')


def logout_view(request):
    try:
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect('/')  # Redirect to login page
    except Exception as e:
        logger.error(f"Error in logout_view: {str(e)}")
        return redirect('/')


@login_required(login_url='/')
def search_view(request):
    try:
        return render(request, 'home/search.html')
    except Exception as e:
        logger.error(f"Error in search_view: {str(e)}")
        messages.error(request, "Unable to load search page.")
        return redirect('home')


@login_required(login_url='/')
def watchlist_view(request):
    try:
        watchlist_items = Watchlist.objects.filter(user=request.user).select_related('movie').prefetch_related('movie__genres', 'movie__language')
        movies = [item.movie for item in watchlist_items]
        return render(request, 'home/watchlist.html', {
            'movies': movies,
            'watchlist_count': len(movies)
        })
    except Exception as e:
        logger.error(f"Error in watchlist_view: {str(e)}")
        messages.error(request, "Unable to load watchlist.")
        return redirect('home')


@login_required(login_url='/')
def profile_view(request):
    try:
        from movies.models import Favorite, Review
        watch_count = WatchHistory.objects.filter(user=request.user).count()
        favorites = Favorite.objects.filter(user=request.user).select_related('movie').prefetch_related('movie__genres').order_by('-added_on')

        # Attach user's own review to each favorite
        fav_list = []
        for fav in favorites:
            review = Review.objects.filter(user=request.user, movie=fav.movie).first()
            fav_list.append({'fav': fav, 'review': review})

        return render(request, 'home/profile.html', {
            'user': request.user,
            'watch_count': watch_count,
            'favorites': fav_list,
        })
    except Exception as e:
        logger.error(f"Error in profile_view: {str(e)}")
        messages.error(request, "Unable to load profile.")
        return redirect('home')


@login_required(login_url='/')
def watch_history_view(request):
    try:
        watch_history = WatchHistory.objects.filter(user=request.user).select_related('movie').order_by('-watched_at')
        return render(request, 'home/watch_history.html', {
            'watch_history': watch_history
        })
    except Exception as e:
        logger.error(f"Error in watch_history_view: {str(e)}")
        messages.error(request, "Unable to load watch history.")
        return redirect('home')


@login_required(login_url='/')
def edit_profile_view(request):
    try:
        if request.method == 'POST':
            # Update user information
            user = request.user
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name = request.POST.get('last_name', '').strip()
            user.email = request.POST.get('email', '').strip()
            
            # Check if username is being changed and if it's available
            new_username = request.POST.get('username', '').strip()
            if new_username != user.username:
                from django.contrib.auth.models import User
                if User.objects.filter(username=new_username).exists():
                    messages.error(request, "Username already exists. Please choose a different one.")
                    return render(request, 'home/edit_profile.html')
                user.username = new_username
            
            user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
        
        return render(request, 'home/edit_profile.html')
    except Exception as e:
        logger.error(f"Error in edit_profile_view: {str(e)}")
        messages.error(request, "Unable to update profile. Please try again.")
        return render(request, 'home/edit_profile.html')


def get_recommended_movies(user, min_interactions=1):
    """
    Get personalized movie recommendations using collaborative filtering.
    
    Args:
        user: The user to get recommendations for
        min_interactions: Minimum number of interactions user must have before getting recommendations
    """
    if not user.is_authenticated:
        return []
    
    # Check if user has enough interactions
    interaction_count = UserInteraction.objects.filter(user=user).count()
    if interaction_count < min_interactions:
        return None  # Indicates new user
    
    # Use the collaborative filtering method from Movie model
    recommended_movies = Movie.get_recommendations_for_user(user, limit=12)
    
    return list(recommended_movies)


def home_page(request):
    try:

        recent_movies = Movie.objects.filter(is_published=True).select_related('language').prefetch_related('genres').order_by('-id')[:8]
        
    
        trending_movies = Movie.objects.filter(is_published=True).select_related('language').prefetch_related('genres').order_by('-views')[:8]
        
        
        recommended_movies = None
        is_new_user = False
        
        if request.user.is_authenticated:
            
            recommended_movies = get_recommended_movies(request.user, min_interactions=1)
            if recommended_movies is None:
                
                is_new_user = True
                recommended_movies = []
        
        return render(request, 'home/homepage.html', {
            'movies': recent_movies,
            'trending_movies': trending_movies,
            'recommended_movies': recommended_movies,
            'is_new_user': is_new_user,
        })
    except Exception as e:
        logger.error(f"Error loading home page: {str(e)}")
        messages.error(request, "Unable to load movies. Please refresh the page.")
        return render(request, 'home/homepage.html', {
            'movies': [], 
            'trending_movies': [],
            'recommended_movies': [],
            'is_new_user': False,
        })


def homepage_view(request):
    try:
        user_watchlist_ids = []
        user_favorite_ids = []
        if request.user.is_authenticated:
            user_watchlist_ids = list(Watchlist.objects.filter(user=request.user).values_list('movie_id', flat=True))
            user_favorite_ids = list(Favorite.objects.filter(user=request.user).values_list('movie_id', flat=True))
        return render(request, 'home/homepage.html', {
            'user_watchlist_ids': user_watchlist_ids,
            'user_favorite_ids': user_favorite_ids,
        })
    except Exception as e:
        logger.error(f"Error in homepage_view: {str(e)}")
        messages.error(request, "Unable to load homepage.")
        return render(request, 'home/homepage.html', {'user_watchlist_ids': [], 'user_favorite_ids': []})



@login_required(login_url='/')
def search_movies_api(request):
    """
    Optional API endpoint for searching movies via AJAX.
    This allows backend filtering instead of client-side only.
    """
    try:
        query = request.GET.get('q', '').strip()
        language = request.GET.get('language', '')
        genres = request.GET.getlist('genres[]')
        
        
        movies = Movie.objects.filter(is_published=True)
        
    
        if query:
            movies = movies.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(cast__icontains=query)
            )
        
        
        if language:
            movies = movies.filter(language__name=language)
        
        
        if genres:
            for genre in genres:
                movies = movies.filter(genres__name__icontains=genre)
        
        
        movies = movies.select_related('language').prefetch_related('genres').distinct()[:50]
        
        
        data = [{
            'id': movie.id,
            'title': movie.title,
            'year': movie.year,
            'description': movie.description or '',
            'thumbnail': movie.thumbnail.url if movie.thumbnail else '',
            'video': movie.video.url if movie.video else '',
            'genres': movie.get_genres_display(),
            'language': movie.language.name if movie.language else 'Unknown',
            'cast': movie.cast or '',
            'rating': float(movie.review_stars) if hasattr(movie, 'review_stars') else 0.0,
            'views': movie.views if hasattr(movie, 'views') else 0,
            'length': movie.movie_length if hasattr(movie, 'movie_length') else 'Unknown',
        } for movie in movies]
        
        return JsonResponse({
            'status': 'success',
            'count': len(data),
            'movies': data
        })
        
    except Exception as e:
        logger.error(f"Error in search_movies_api: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while searching movies.'
        }, status=500)



# -----------------------------------------------------------------------
# eSewa Helper Functions
# -----------------------------------------------------------------------

def _generate_signature(total_amount, transaction_uuid, product_code):
    """HMAC-SHA256 signature required by eSewa v2."""
    message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    sig = hmac.new(
        ESEWA_SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(sig).decode('utf-8')


def _callback_base(request):
    """Return the base URL for eSewa callbacks."""
    if ESEWA_CALLBACK_BASE:
        return ESEWA_CALLBACK_BASE.rstrip('/')
    return request.build_absolute_uri('/').rstrip('/')


def _check_esewa_status(transaction_uuid, total_amount):
    """Query eSewa v2 status API. Returns (status_str, ref_id)."""
    try:
        url = (
            f"{ESEWA_STATUS_URL}"
            f"?product_code={ESEWA_MERCHANT_CODE}"
            f"&total_amount={total_amount}"
            f"&transaction_uuid={transaction_uuid}"
        )
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('status'), data.get('ref_id')
    except Exception as e:
        logger.error(f"eSewa status check error: {e}")
    return None, None


# -----------------------------------------------------------------------
# Payment Views
# -----------------------------------------------------------------------

@login_required(login_url='/')
def payment_view(request):
    # Already paid — go straight to dashboard
    if Payment.objects.filter(user=request.user, status='completed').exists():
        return redirect('home')

    if request.method == 'POST':
        transaction_uuid = uuid.uuid4().hex  # no hyphens — eSewa v2 requirement

        Payment.objects.create(
            user=request.user,
            transaction_id=transaction_uuid,
            amount=SUBSCRIPTION_AMOUNT,
        )

        signature = _generate_signature(SUBSCRIPTION_AMOUNT, transaction_uuid, ESEWA_MERCHANT_CODE)
        base = _callback_base(request)

        esewa_config = {
            'amount':                   SUBSCRIPTION_AMOUNT,
            'tax_amount':               '0',
            'total_amount':             SUBSCRIPTION_AMOUNT,
            'transaction_uuid':         transaction_uuid,
            'product_code':             ESEWA_MERCHANT_CODE,
            'product_service_charge':   '0',
            'product_delivery_charge':  '0',
            'success_url':              f"{base}/payment/success/",
            'failure_url':              f"{base}/payment/failure/",
            'signed_field_names':       'total_amount,transaction_uuid,product_code',
            'signature':                signature,
            'esewa_url':                ESEWA_PAYMENT_URL,
        }

        return render(request, 'home/payment_redirect.html', {'esewa_config': esewa_config})

    return render(request, 'home/payment.html')


@csrf_exempt
def payment_success_view(request):
    """
    eSewa v2 redirects here with ?data=<base64-encoded-json> after payment.
    """
    raw = request.GET.get('data') or request.POST.get('data')

    if raw:
        try:
            response_data = json.loads(base64.b64decode(raw).decode('utf-8'))
            transaction_uuid = response_data.get('transaction_uuid')
            status           = response_data.get('status')
            ref_id           = response_data.get('transaction_code', '')

            if not transaction_uuid:
                raise ValueError("Missing transaction_uuid in eSewa response")

            try:
                payment = Payment.objects.get(transaction_id=transaction_uuid)
            except Payment.DoesNotExist:
                logger.error(f"No payment record for transaction_uuid={transaction_uuid}")
                messages.error(request, 'Payment record not found. Please contact support.')
                return redirect('payment')

            if status == 'COMPLETE':
                payment.status       = 'completed'
                payment.esewa_ref_id = ref_id
                payment.save()

                # Re-authenticate user if session was lost during eSewa redirect
                if not request.user.is_authenticated:
                    user = payment.user
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)

                messages.success(request, 'Payment successful! Enjoy unlimited streaming.')
                return redirect('home')

            else:
                # Status is not COMPLETE — double-check with eSewa API
                esewa_status, api_ref = _check_esewa_status(transaction_uuid, SUBSCRIPTION_AMOUNT)
                if esewa_status == 'COMPLETE':
                    payment.status       = 'completed'
                    payment.esewa_ref_id = api_ref or ref_id
                    payment.save()
                    messages.success(request, 'Payment verified. Enjoy unlimited streaming.')
                    return redirect('home')

                payment.status = 'failed'
                payment.save()
                messages.error(request, f'Payment not completed (status: {status}). Please try again.')
                return redirect('payment')

        except Exception as e:
            logger.error(f"payment_success_view error: {e}")
            messages.error(request, 'Payment verification failed. Please contact support.')
            return redirect('payment')

    messages.error(request, 'Invalid payment response received.')
    return redirect('payment')


@csrf_exempt
def payment_failure_view(request):
    messages.error(request, 'Payment was cancelled or failed. Please try again.')
    return redirect('payment')


@login_required(login_url='/')
def verify_payment_status(request, transaction_uuid):
    """Manual re-verification endpoint (called by frontend polling if needed)."""
    try:
        payment = Payment.objects.get(transaction_id=transaction_uuid, user=request.user)

        if payment.status == 'completed':
            return JsonResponse({'status': 'success', 'message': 'Payment already completed'})

        esewa_status, ref_id = _check_esewa_status(transaction_uuid, str(payment.amount))

        if esewa_status == 'COMPLETE':
            payment.status       = 'completed'
            payment.esewa_ref_id = ref_id
            payment.save()
            return JsonResponse({'status': 'success', 'message': 'Payment verified'})

        if esewa_status in ('PENDING', 'AMBIGUOUS'):
            return JsonResponse({'status': 'pending', 'message': 'Payment still processing'})

        return JsonResponse({'status': 'failed', 'message': 'Payment verification failed'})

    except Payment.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Payment not found'}, status=404)
    except Exception as e:
        logger.error(f"verify_payment_status error: {e}")
        return JsonResponse({'status': 'error', 'message': 'Verification error'}, status=500)


# -----------------------------------------------------------------------
# Footer Pages
# -----------------------------------------------------------------------

def faq_view(request):
    faqs = [
        ("What is JetFlix?", "JetFlix is a streaming platform where you can watch movies in high definition with no advertisements."),
        ("How much does it cost?", "JetFlix requires a one-time payment of Rs. 500 for lifetime access to all content."),
        ("How do I pay?", "We accept payments via eSewa. Click 'Pay with eSewa' on the payment page and follow the steps."),
        ("Can I watch on multiple devices?", "Yes, you can access JetFlix from any device with a modern web browser."),
        ("What video quality is available?", "All movies are available in high definition (HD) quality."),
        ("How do I reset my password?", "Contact us at support@jetflix.com and we'll help you reset your password."),
        ("Can I download movies?", "Currently JetFlix supports online streaming only. Downloads are not available."),
        ("How do I add movies to my watchlist?", "Click the bookmark icon on any movie card to add it to your watchlist."),
    ]
    return render(request, 'home/faq.html', {'faqs': faqs})


def privacy_view(request):
    sections = [
        {"title": "1. Information We Collect", "body": "We collect information you provide when registering, such as your username and email address. We also collect usage data such as movies watched and watchlist activity to improve your experience."},
        {"title": "2. How We Use Your Information", "body": "Your information is used to provide and improve our service, process payments, and communicate with you about your account. We do not sell your personal data to third parties."},
        {"title": "3. Payment Information", "body": "Payments are processed securely through eSewa. JetFlix does not store your payment credentials. All transactions are encrypted and handled by eSewa's secure payment gateway."},
        {"title": "4. Cookies", "body": "We use session cookies to keep you logged in and remember your preferences. These cookies are essential for the service to function and do not track you across other websites."},
        {"title": "5. Data Security", "body": "We implement industry-standard security measures to protect your personal information. Your password is stored as a secure hash and is never accessible in plain text."},
        {"title": "6. Your Rights", "body": "You have the right to access, update, or delete your personal information at any time. Contact us at support@jetflix.com to exercise these rights."},
        {"title": "7. Contact", "body": "If you have any questions about this Privacy Policy, please contact us at support@jetflix.com."},
    ]
    return render(request, 'home/privacy.html', {'sections': sections})


def terms_view(request):
    sections = [
        {"title": "1. Acceptance of Terms", "body": "By accessing and using JetFlix, you accept and agree to be bound by these Terms of Use. If you do not agree, please do not use our service."},
        {"title": "2. Account Registration", "body": "You must register for an account to use JetFlix. You are responsible for maintaining the confidentiality of your account credentials and for all activities under your account."},
        {"title": "3. Payment", "body": "Access to JetFlix requires a one-time payment of Rs. 500. This grants you lifetime access to all available content. Payments are non-refundable once processed."},
        {"title": "4. Content Usage", "body": "All content on JetFlix is for personal, non-commercial use only. You may not download, reproduce, distribute, or publicly display any content without prior written permission."},
        {"title": "5. Prohibited Conduct", "body": "You agree not to use JetFlix for any unlawful purpose, to attempt to gain unauthorized access to any part of the service, or to interfere with the proper functioning of the platform."},
        {"title": "6. Termination", "body": "We reserve the right to suspend or terminate your account at any time if you violate these terms or engage in conduct harmful to other users or the platform."},
        {"title": "7. Changes to Terms", "body": "We may update these Terms of Use from time to time. Continued use of JetFlix after changes constitutes acceptance of the new terms."},
    ]
    return render(request, 'home/terms.html', {'sections': sections})


def help_view(request):
    topics = [
        {"title": "Getting Started", "body": "Create an account, complete your one-time payment, and start watching immediately. No subscription required."},
        {"title": "Payment Issues", "body": "If your payment failed, check your eSewa balance and try again. Contact us if the issue persists."},
        {"title": "Video Playback", "body": "For the best experience use a modern browser like Chrome or Firefox. Make sure your internet connection is stable."},
        {"title": "Account Settings", "body": "Update your username, email, and other details from your Profile page accessible via the top navigation."},
        {"title": "Watchlist", "body": "Save movies to your watchlist by clicking the bookmark icon. Access your watchlist from the navigation bar."},
        {"title": "Watch History", "body": "Your recently watched movies are saved automatically. View them from the dropdown menu under your profile."},
    ]
    return render(request, 'home/help.html', {'topics': topics})


def contact_view(request):
    sent = False
    if request.method == 'POST':
        # In production connect this to an email backend
        sent = True
    return render(request, 'home/contact.html', {'sent': sent})


def legal_view(request):
    sections = [
        {"title": "Copyright Notice", "body": "All content, trademarks, and intellectual property on JetFlix are the property of their respective owners. JetFlix does not claim ownership of any third-party content displayed on the platform."},
        {"title": "Disclaimer of Warranties", "body": "JetFlix is provided 'as is' without warranties of any kind. We do not guarantee uninterrupted or error-free service and are not liable for any damages arising from use of the platform."},
        {"title": "Limitation of Liability", "body": "To the maximum extent permitted by law, JetFlix shall not be liable for any indirect, incidental, or consequential damages arising out of your use of the service."},
        {"title": "Governing Law", "body": "These terms are governed by the laws of Nepal. Any disputes shall be resolved in the courts of Kathmandu, Nepal."},
        {"title": "Third-Party Services", "body": "JetFlix uses eSewa for payment processing. Use of eSewa is subject to eSewa's own terms and privacy policy."},
    ]
    return render(request, 'home/legal.html', {'sections': sections})
