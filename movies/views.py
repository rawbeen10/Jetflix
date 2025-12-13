from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Movie, Watchlist
import json

def landing_page(request):
    movies = Movie.objects.filter(is_published=True)
    
    # Get user's watchlist IDs if logged in
    user_watchlist_ids = []
    if request.user.is_authenticated:
        user_watchlist_ids = list(
            Watchlist.objects.filter(user=request.user).values_list('movie_id', flat=True)
        )
    
    return render(request, 'movies/landing.html', {
        'movies': movies,
        'user_watchlist_ids': user_watchlist_ids
    })

@login_required
def watchlist_page(request):
    watchlist_items = Watchlist.objects.filter(user=request.user).select_related('movie')
    movies = [item.movie for item in watchlist_items]
    
    return render(request, 'movies/watchlist.html', {
        'movies': movies,
        'watchlist_count': len(movies)
    })

@login_required
@require_POST
def add_to_watchlist(request):
    try:
        data = json.loads(request.body)
        movie_id = data.get('movie_id')
        
        movie = Movie.objects.get(id=movie_id)
        watchlist_item, created = Watchlist.objects.get_or_create(
            user=request.user,
            movie=movie
        )
        
        if created:
            return JsonResponse({
                'status': 'success',
                'message': 'Added to watchlist',
                'action': 'added'
            })
        else:
            return JsonResponse({
                'status': 'success',
                'message': 'Already in watchlist',
                'action': 'exists'
            })
    except Movie.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Movie not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def remove_from_watchlist(request):
    try:
        data = json.loads(request.body)
        movie_id = data.get('movie_id')
        
        Watchlist.objects.filter(user=request.user, movie_id=movie_id).delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Removed from watchlist'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)