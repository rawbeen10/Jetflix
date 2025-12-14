from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .forms import CustomUserCreationForm
from movies.models import Movie
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
def watch_history_view(request):
    try:
        return render(request, 'home/watch_history.html')
    except Exception as e:
        logger.error(f"Error in watch_history_view: {str(e)}")
        messages.error(request, "Unable to load watch history.")
        return redirect('home')


@login_required(login_url='login')
def edit_profile_view(request):
    try:
        return render(request, 'home/edit_profile.html')
    except Exception as e:
        logger.error(f"Error in edit_profile_view: {str(e)}")
        messages.error(request, "Unable to load profile editor.")
        return redirect('home')


def home_page(request):
    try:
        # Get the 8 most recently added movies with prefetch
        recent_movies = Movie.objects.filter(is_published=True).select_related('language').prefetch_related('genres').order_by('-id')[:8]
        
        # Get trending movies (top 8 by views)
        trending_movies = Movie.objects.filter(is_published=True).select_related('language').prefetch_related('genres').order_by('-views')[:8]
        
        # Get ALL movies for search sidebar (only if user is authenticated)
        all_movies = []
        if request.user.is_authenticated:
            all_movies = Movie.objects.filter(is_published=True).select_related('language').prefetch_related('genres').all()
        
        return render(request, 'home/homepage.html', {
            'movies': recent_movies,
            'trending_movies': trending_movies,
            'all_movies': all_movies,  # For search sidebar
        })
    except Exception as e:
        logger.error(f"Error loading home page: {str(e)}")
        messages.error(request, "Unable to load movies. Please refresh the page.")
        return render(request, 'home/homepage.html', {
            'movies': [], 
            'trending_movies': [],
            'all_movies': []
        })


def homepage_view(request):
    try:
        # Get ALL movies for search sidebar (only if user is authenticated)
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


# OPTIONAL: API endpoint for AJAX search (if you want real-time backend search)
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
        
        # Start with all published movies
        movies = Movie.objects.filter(is_published=True)
        
        # Apply search query
        if query:
            movies = movies.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(cast__icontains=query)
            )
        
        # Apply language filter
        if language:
            movies = movies.filter(language__name=language)
        
        # Apply genre filter
        if genres:
            for genre in genres:
                movies = movies.filter(genres__name__icontains=genre)
        
        # Get results with related data
        movies = movies.select_related('language').prefetch_related('genres').distinct()[:50]
        
        # Format response
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