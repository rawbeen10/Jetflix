from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from .forms import CustomUserCreationForm
from .models import Payment
from movies.models import Movie, Watchlist, WatchHistory, UserInteraction
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
ESEWA_PAYMENT_URL    = 'https://rc-epay.esewa.com.np/epay/main'
ESEWA_STATUS_URL     = 'https://rc.esewa.com.np/api/epay/transaction/status/'
SUBSCRIPTION_AMOUNT  = '500'

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
        watch_count = WatchHistory.objects.filter(user=request.user).count()
        return render(request, 'home/profile.html', {
            'user': request.user,
            'watch_count': watch_count,
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
        if request.user.is_authenticated:
            user_watchlist_ids = list(
                Watchlist.objects.filter(user=request.user).values_list('movie_id', flat=True)
            )
        return render(request, 'home/homepage.html', {'user_watchlist_ids': user_watchlist_ids})
    except Exception as e:
        logger.error(f"Error in homepage_view: {str(e)}")
        messages.error(request, "Unable to load homepage.")
        return render(request, 'home/homepage.html', {'user_watchlist_ids': []})



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
        transaction_uuid = str(uuid.uuid4())

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
