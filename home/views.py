from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from .forms import CustomUserCreationForm
from .models import Payment
from movies.models import Movie, WatchHistory, UserInteraction
import logging
import uuid
import hashlib
import hmac
import base64
import json
import requests

# eSewa Configuration
ESEWA_MERCHANT_CODE = 'EPAYTEST'
ESEWA_SECRET_KEY = '8gBm/:&EnhH.1/q'
ESEWA_SANDBOX_URL = 'https://rc-epay.esewa.com.np/api/epay/main/v2/form'
ESEWA_STATUS_URL = 'https://rc.esewa.com.np/api/epay/transaction/status/'

def generate_esewa_signature(total_amount, transaction_uuid, product_code):
    """Generate HMAC SHA256 signature for eSewa"""
    message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    signature = hmac.new(
        ESEWA_SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode('utf-8')

def check_esewa_payment_status(transaction_uuid, total_amount):
    """Check payment status with eSewa API"""
    try:
        url = f"{ESEWA_STATUS_URL}?product_code={ESEWA_MERCHANT_CODE}&total_amount={total_amount}&transaction_uuid={transaction_uuid}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('status'), data.get('ref_id')
        else:
            return None, None
    except Exception:
        return None, None

logger = logging.getLogger(__name__)


# Home / Register
def register_view(request):
    try:
        if request.method == 'POST':
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                user = form.save()
                login(request, user)  # Auto-login after registration
                messages.success(request, "Account created successfully! Please complete payment to access movies.")
                return redirect('payment')
            else:
                # Return to login page with signup form active and errors
                return render(request, 'home/login.html', {
                    'show_signup': True,
                    'signup_errors': form.errors
                })
        else:
            form = CustomUserCreationForm()
        return render(request, 'home/login.html', {'show_signup': True})
    except Exception as e:
        logger.error(f"Error in register_view: {str(e)}")
        messages.error(request, "An error occurred during registration. Please try again.")
        return render(request, 'home/login.html', {'show_signup': True})


# Login
def login_view(request):
    # Redirect authenticated users with payment to dashboard
    if request.user.is_authenticated:
        has_payment = Payment.objects.filter(
            user=request.user, 
            status='completed'
        ).exists()
        
        if has_payment:
            return redirect('home')
        else:
            return redirect('payment')
    
    try:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Check if user has active payment
                has_payment = Payment.objects.filter(
                    user=user, 
                    status='completed'
                ).exists()
                
                if has_payment:
                    messages.success(request, f"Welcome back, {user.username}!")
                    return redirect('home')
                else:
                    return redirect('payment')
            else:
                messages.error(request, "Invalid email or password.")
        
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
        return render(request, 'home/watchlist.html')
    except Exception as e:
        logger.error(f"Error in watchlist_view: {str(e)}")
        messages.error(request, "Unable to load watchlist.")
        return redirect('home')


@login_required(login_url='/')
def profile_view(request):
    try:
        # Get user's watch history count
        watch_count = WatchHistory.objects.filter(user=request.user).count()
        
        return render(request, 'home/profile.html', {
            'user': request.user,
            'watch_count': watch_count
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


def get_recommended_movies(user, min_interactions=2):
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
    recommended_movies = Movie.get_recommendations_for_user(user, limit=8)
    
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
        
        
        all_movies = []
        if request.user.is_authenticated:
            all_movies = Movie.objects.filter(is_published=True).select_related('language').prefetch_related('genres').all()
        
        return render(request, 'home/homepage.html', {
            'movies': recent_movies,
            'trending_movies': trending_movies,
            'recommended_movies': recommended_movies,
            'is_new_user': is_new_user,
            'all_movies': all_movies, 
        })
    except Exception as e:
        logger.error(f"Error loading home page: {str(e)}")
        messages.error(request, "Unable to load movies. Please refresh the page.")
        return render(request, 'home/homepage.html', {
            'movies': [], 
            'trending_movies': [],
            'recommended_movies': [],
            'is_new_user': False,
            'all_movies': []
        })


def homepage_view(request):
    try:
        
        all_movies = []
        if request.user.is_authenticated:
            all_movies = Movie.objects.filter(is_published=True).select_related('language').prefetch_related('genres').all()
        
        return render(request, 'home/homepage.html', {
            'all_movies': all_movies
        })
    except Exception as e:
        logger.error(f"Error in homepage_view: {str(e)}")
        messages.error(request, "Unable to load homepage.")
        return render(request, 'home/homepage.html', {'all_movies': []})



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


@login_required(login_url='/')
def verify_payment_status(request, transaction_uuid):
    """Manual payment verification endpoint"""
    try:
        payment = Payment.objects.get(transaction_id=transaction_uuid, user=request.user)
        
        if payment.status == 'completed':
            return JsonResponse({'status': 'success', 'message': 'Payment already completed'})
        
        # Check with eSewa
        esewa_status, ref_id = check_esewa_payment_status(transaction_uuid, str(payment.amount))
        
        if esewa_status == 'COMPLETE':
            payment.status = 'completed'
            payment.esewa_ref_id = ref_id
            payment.save()
            return JsonResponse({'status': 'success', 'message': 'Payment verified and completed'})
        elif esewa_status in ['PENDING', 'AMBIGUOUS']:
            return JsonResponse({'status': 'pending', 'message': 'Payment is still processing'})
        else:
            return JsonResponse({'status': 'failed', 'message': 'Payment verification failed'})
            
    except Payment.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Payment not found'})
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        return JsonResponse({'status': 'error', 'message': 'Verification failed'})


@login_required(login_url='/')
def payment_view(request):
    # Check if user already has active payment
    active_payment = Payment.objects.filter(
        user=request.user,
        status='completed'
    ).first()
    
    if active_payment:
        return redirect('home')
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        if payment_method == 'esewa':
            # Create payment record for eSewa
            transaction_uuid = str(uuid.uuid4())
            payment = Payment.objects.create(
                user=request.user,
                transaction_id=transaction_uuid,
                amount=500.00
            )
            
            # Generate signature
            signature = generate_esewa_signature('500', transaction_uuid, ESEWA_MERCHANT_CODE)
            
            # eSewa form data
            esewa_config = {
                'amount': '500',
                'tax_amount': '0',
                'total_amount': '500',
                'transaction_uuid': transaction_uuid,
                'product_code': ESEWA_MERCHANT_CODE,
                'product_service_charge': '0',
                'product_delivery_charge': '0',
                'success_url': request.build_absolute_uri('/payment/success/'),
                'failure_url': request.build_absolute_uri('/payment/failure/'),
                'signed_field_names': 'total_amount,transaction_uuid,product_code',
                'signature': signature,
                'esewa_url': ESEWA_SANDBOX_URL
            }
            
            return render(request, 'home/payment_redirect.html', {
                'payment': payment,
                'esewa_config': esewa_config
            })
    
    return render(request, 'home/payment.html')


def payment_success_view(request):
    # Get response data from eSewa
    data = request.GET.get('data')
    
    if data:
        try:
            # Decode base64 response
            decoded_data = base64.b64decode(data).decode('utf-8')
            response_data = json.loads(decoded_data)
            
            transaction_uuid = response_data.get('transaction_uuid')
            status = response_data.get('status')
            
            if transaction_uuid and status == 'COMPLETE':
                payment = Payment.objects.get(transaction_id=transaction_uuid)
                payment.status = 'completed'
                payment.esewa_ref_id = response_data.get('transaction_code', '')
                payment.save()
                
                messages.success(request, 'Payment successful! You now have access to all movies.')
                return redirect('/')  # Redirect to login page
        except (Payment.DoesNotExist, json.JSONDecodeError, Exception) as e:
            logger.error(f"Payment verification failed: {e}")
            messages.error(request, 'Payment verification failed.')
    
    # Fallback for old format
    transaction_id = request.GET.get('oid')
    if transaction_id:
        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
            payment.status = 'completed'
            payment.esewa_ref_id = request.GET.get('refId', f'esewa_ref_{transaction_id[:8]}')
            payment.save()
            
            messages.success(request, 'Payment successful! You now have access to all movies.')
            return redirect('/')  # Redirect to login page
        except Payment.DoesNotExist:
            messages.error(request, 'Payment verification failed.')
    
    # No success message here - only redirect if no valid payment found
    return redirect('payment')


def payment_failure_view(request):
    messages.error(request, 'Payment failed. Please try again.')
    return redirect('payment')