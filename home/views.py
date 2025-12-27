from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count
from .forms import CustomUserCreationForm
from movies.models import Movie, WatchHistory, UserInteraction
import logging

logger = logging.getLogger(__name__)


# Home / Register
def register_view(request):
    try:
        if request.method == 'POST':
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Account created successfully! You can now log in.")
                return redirect('login')
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            form = CustomUserCreationForm()
        return render(request, 'home/register.html', {'form': form})
    except Exception as e:
        logger.error(f"Error in register_view: {str(e)}")
        messages.error(request, "An error occurred during registration. Please try again.")
        return render(request, 'home/register.html', {'form': CustomUserCreationForm()})


# Login
def login_view(request):
    try:
        if request.method == 'POST':
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                
                # Check if there's a 'next' parameter (where to redirect after login)
                next_url = request.GET.get('next') or request.POST.get('next')
                if next_url:
                    return redirect(next_url)
                
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('home')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            form = AuthenticationForm()
        return render(request, 'home/login.html', {'form': form})
    except Exception as e:
        logger.error(f"Error in login_view: {str(e)}")
        messages.error(request, "An error occurred during login. Please try again.")
        return render(request, 'home/login.html', {'form': AuthenticationForm()})


def logout_view(request):
    try:
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect('home')
    except Exception as e:
        logger.error(f"Error in logout_view: {str(e)}")
        return redirect('home')


@login_required(login_url='login')
def search_view(request):
    try:
        return render(request, 'home/search.html')
    except Exception as e:
        logger.error(f"Error in search_view: {str(e)}")
        messages.error(request, "Unable to load search page.")
        return redirect('home')


@login_required(login_url='login')
def watchlist_view(request):
    try:
        return render(request, 'home/watchlist.html')
    except Exception as e:
        logger.error(f"Error in watchlist_view: {str(e)}")
        messages.error(request, "Unable to load watchlist.")
        return redirect('home')


@login_required(login_url='login')
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


@login_required(login_url='login')
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


@login_required(login_url='login')
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



@login_required(login_url='login')
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