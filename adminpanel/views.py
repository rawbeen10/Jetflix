from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import MovieForm
from movies.models import Movie


def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid admin credentials')

    return render(request, 'adminpanel/login.html')

@staff_member_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_movies = Movie.objects.count()
    published_movies = Movie.objects.filter(is_published=True).count()
    total_views = sum(movie.views for movie in Movie.objects.all())

    context = {
        'total_users': total_users,
        'total_movies': total_movies,
        'published_movies': published_movies,
        'total_views': total_views,
    }

    return render(request, 'adminpanel/dashboard.html', context)

@staff_member_required
def add_movie(request):
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES)
        if form.is_valid():
            movie = form.save()
            messages.success(request, f'Movie "{movie.title}" added successfully!')
            return redirect('admin-all-movies')
    else:
        form = MovieForm()

    return render(request, 'adminpanel/add_movie.html', {'form': form})

@staff_member_required
def all_movies(request):
    movies = Movie.objects.all().order_by('-id')
    return render(request, 'adminpanel/all_movies.html', {'movies': movies})

@staff_member_required
def edit_movie(request, movie_id):
    """Edit an existing movie"""
    movie = get_object_or_404(Movie, id=movie_id)
    
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES, instance=movie)
        if form.is_valid():
            movie = form.save()
            messages.success(request, f'Movie "{movie.title}" updated successfully!')
            return redirect('admin-all-movies')
    else:
        form = MovieForm(instance=movie)
    
    return render(request, 'adminpanel/edit_movie.html', {'form': form, 'movie': movie})

@staff_member_required
@require_POST
def delete_movie(request, movie_id):
    """Delete a movie"""
    try:
        movie = get_object_or_404(Movie, id=movie_id)
        movie_title = movie.title
        
        # Delete the movie files if they exist
        if movie.thumbnail:
            movie.thumbnail.delete()
        if movie.video:
            movie.video.delete()
        
        movie.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Movie "{movie_title}" deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)