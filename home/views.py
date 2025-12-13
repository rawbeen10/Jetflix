from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
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
        # Get the 8 most recently added movies
        recent_movies = Movie.objects.filter(is_published=True).order_by('-id')[:8]
        
        return render(request, 'home/homepage.html', {
            'movies': recent_movies
        })
    except Exception as e:
        logger.error(f"Error loading home page: {str(e)}")
        messages.error(request, "Unable to load movies. Please refresh the page.")
        return render(request, 'home/homepage.html', {'movies': []})


def homepage_view(request):
    try:
        return render(request, 'home/homepage.html')
    except Exception as e:
        logger.error(f"Error in homepage_view: {str(e)}")
        messages.error(request, "Unable to load homepage.")
        return render(request, 'home/homepage.html')