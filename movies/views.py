from django.utils import timezone   # ← FIXED: was "from datetime import timezone"

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import F, Count, Q
from .models import Movie, Watchlist, Review, WatchHistory, UserInteraction, Favorite, Genre, Language
import json


def landing_page(request):
    movies = Movie.objects.filter(
        is_published=True
    ).select_related('language').prefetch_related('genres').order_by('-id')

    user_watchlist_ids = []
    user_favorite_ids = []
    if request.user.is_authenticated:
        user_watchlist_ids = list(
            Watchlist.objects.filter(user=request.user).values_list('movie_id', flat=True)
        )
        user_favorite_ids = list(
            Favorite.objects.filter(user=request.user).values_list('movie_id', flat=True)
        )

    genres = Genre.objects.annotate(
        movie_count=Count('movies', filter=Q(movies__is_published=True))
    ).filter(movie_count__gt=0).order_by('name')

    languages = Language.objects.annotate(
        movie_count=Count('movies', filter=Q(movies__is_published=True))
    ).filter(movie_count__gt=0).order_by('name')

    return render(request, 'movies/landing.html', {
        'movies': movies,
        'user_watchlist_ids': user_watchlist_ids,
        'user_favorite_ids': user_favorite_ids,
        'genres': genres,
        'languages': languages,
    })


@login_required
def watchlist_page(request):
    watchlist_items = Watchlist.objects.filter(
        user=request.user
    ).select_related('movie').prefetch_related('movie__genres', 'movie__language')
    movies = [item.movie for item in watchlist_items]
    user_favorite_ids = list(
        Favorite.objects.filter(user=request.user).values_list('movie_id', flat=True)
    )
    return render(request, 'movies/watchlist.html', {
        'movies': movies,
        'watchlist_count': len(movies),
        'user_favorite_ids': user_favorite_ids,
    })


# -----------------------------------------------------------------------
# Watchlist API
# -----------------------------------------------------------------------

@login_required
@require_POST
def add_to_watchlist(request):
    try:
        data = json.loads(request.body)
        movie_id = data.get('movie_id')

        movie = get_object_or_404(Movie, id=movie_id)
        watchlist_item, created = Watchlist.objects.get_or_create(
            user=request.user,
            movie=movie
        )

        if created:
            # FIXED: use create (not get_or_create) so every watchlist action
            # is recorded as a fresh interaction for recency-based recommendations
            UserInteraction.objects.create(
                user=request.user,
                movie=movie,
                interaction_type='watchlist',
                score=1.0,
                created_at=timezone.now()
            )
            return JsonResponse({'status': 'success', 'action': 'added'})
        else:
            return JsonResponse({'status': 'success', 'action': 'already_exists'})

    except Movie.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Movie not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def remove_from_watchlist(request):
    try:
        data = json.loads(request.body)
        movie_id = data.get('movie_id')

        Watchlist.objects.filter(user=request.user, movie_id=movie_id).delete()

        return JsonResponse({'status': 'success', 'action': 'removed'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def get_watchlist(request):
    try:
        watchlist_items = Watchlist.objects.filter(
            user=request.user
        ).select_related('movie').prefetch_related('movie__genres', 'movie__language')

        movies_data = [{
            'id':          item.movie.id,
            'title':       item.movie.title,
            'year':        item.movie.year,
            'description': item.movie.description or '',
            'thumbnail':   item.movie.thumbnail.url if item.movie.thumbnail else '',
            'video':       item.movie.video.url if item.movie.video else '',
            'genres':      item.movie.get_genres_display(),
            'language':    item.movie.language.name if item.movie.language else 'Unknown',
            'cast':        item.movie.cast or '',
            'length':      item.movie.movie_length or 'Unknown',
            'rating':      float(item.movie.review_stars),
            'views':       item.movie.views,
        } for item in watchlist_items]

        return JsonResponse({'status': 'success', 'movies': movies_data, 'count': len(movies_data)})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def check_watchlist_status(request, movie_id):
    try:
        in_watchlist = Watchlist.objects.filter(user=request.user, movie_id=movie_id).exists()
        return JsonResponse({'in_watchlist': in_watchlist})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# -----------------------------------------------------------------------
# View Count & Watch History
# -----------------------------------------------------------------------

@login_required
@require_POST
def increment_view(request):
    try:
        data     = json.loads(request.body)
        movie_id = data.get('movie_id')

        movie = get_object_or_404(Movie, id=movie_id)
        movie.views = F('views') + 1
        movie.save(update_fields=['views'])

        WatchHistory.objects.get_or_create(user=request.user, movie=movie)

        # FIXED: always create a fresh interaction so recency weighting works.
        # UserInteraction has no unique_together constraint, so multiple rows
        # per user+movie are intentional — each represents a distinct watch event.
        UserInteraction.objects.create(
            user=request.user,
            movie=movie,
            interaction_type='watch',
            score=2.0,
            created_at=timezone.now()
        )

        movie.refresh_from_db(fields=['views'])
        return JsonResponse({'status': 'success', 'views': movie.views})

    except Movie.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Movie not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# -----------------------------------------------------------------------
# Review API
# -----------------------------------------------------------------------

def get_reviews(request, movie_id):
    try:
        movie = get_object_or_404(Movie, id=movie_id)
        reviews = movie.reviews.select_related('user').all()

        reviews_data = [{
            'id':          review.id,
            'user':        review.user.username,
            'user_id':     review.user.id,
            'rating':      review.rating,
            'review_text': review.review_text,
            'created_at':  review.time_since_created(),
            'is_owner':    request.user.is_authenticated and review.user == request.user,
        } for review in reviews]

        return JsonResponse({
            'status':         'success',
            'reviews':        reviews_data,
            'average_rating': float(movie.review_stars),
            'total_reviews':  len(reviews_data),
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def add_review(request):
    try:
        data        = json.loads(request.body)
        movie_id    = data.get('movie_id')
        rating      = data.get('rating')
        review_text = data.get('review_text', '').strip()

        if not movie_id or not rating:
            return JsonResponse({'status': 'error', 'message': 'Movie ID and rating are required'}, status=400)

        if not (1 <= int(rating) <= 5):
            return JsonResponse({'status': 'error', 'message': 'Rating must be between 1 and 5'}, status=400)

        if len(review_text) > 1000:
            return JsonResponse({'status': 'error', 'message': 'Review text too long (max 1000 characters)'}, status=400)

        movie = get_object_or_404(Movie, id=movie_id)

        review, created = Review.objects.update_or_create(
            user=request.user,
            movie=movie,
            defaults={
                'rating':      int(rating),
                'review_text': review_text,
            }
        )

        # FIXED: timezone.now() now works correctly with the fixed import.
        # Always create a fresh interaction for each review/update so the
        # recency decay in content-based recommendations reflects this action.
        UserInteraction.objects.create(
            user=request.user,
            movie=movie,
            interaction_type='review',
            score=float(rating),
            created_at=timezone.now()
        )

        return JsonResponse({
            'status':  'success',
            'message': 'Review added successfully' if created else 'Review updated successfully',
            'review': {
                'id':          review.id,
                'user':        review.user.username,
                'rating':      review.rating,
                'review_text': review.review_text,
                'created_at':  review.time_since_created(),
                'is_owner':    True,
            },
            'average_rating': float(movie.review_stars),
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def edit_review(request, review_id):
    try:
        data        = json.loads(request.body)
        rating      = data.get('rating')
        review_text = data.get('review_text', '').strip()

        if not rating:
            return JsonResponse({'status': 'error', 'message': 'Rating is required'}, status=400)

        if not (1 <= int(rating) <= 5):
            return JsonResponse({'status': 'error', 'message': 'Rating must be between 1 and 5'}, status=400)

        if len(review_text) > 1000:
            return JsonResponse({'status': 'error', 'message': 'Review text too long (max 1000 characters)'}, status=400)

        review = get_object_or_404(Review, id=review_id, user=request.user)
        review.rating      = int(rating)
        review.review_text = review_text
        review.save()

        return JsonResponse({
            'status':  'success',
            'message': 'Review updated successfully',
            'review': {
                'id':          review.id,
                'user':        review.user.username,
                'rating':      review.rating,
                'review_text': review.review_text,
                'created_at':  review.time_since_created(),
                'is_owner':    True,
            },
            'average_rating': float(review.movie.review_stars),
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def delete_review(request, review_id):
    try:
        review = get_object_or_404(Review, id=review_id, user=request.user)
        movie  = review.movie
        review.delete()

        return JsonResponse({
            'status':         'success',
            'message':        'Review deleted successfully',
            'average_rating': float(movie.review_stars),
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# -----------------------------------------------------------------------
# Recommendation API
# -----------------------------------------------------------------------

def get_similar_movies(request, movie_id):
    try:
        movie = get_object_or_404(Movie, id=movie_id, is_published=True)
        similar_movies = movie.get_similar_movies(limit=6)

        movies_data = [{
            'id':       m.id,
            'title':    m.title,
            'year':     m.year,
            'thumbnail': m.thumbnail.url if m.thumbnail else '',
            'rating':   float(m.review_stars),
            'genres':   m.get_genres_display(),
            'language': m.language.name if m.language else 'Unknown',
        } for m in similar_movies]

        return JsonResponse({'status': 'success', 'movies': movies_data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def get_user_recommendations(request):
    try:
        recommended_movies = Movie.get_recommendations_for_user(request.user, limit=6)

        movies_data = [{
            'id':        m.id,
            'title':     m.title,
            'year':      m.year,
            'thumbnail': m.thumbnail.url if m.thumbnail else '',
            'rating':    float(m.review_stars),
            'genres':    m.get_genres_display(),
            'language':  m.language.name if m.language else 'Unknown',
        } for m in recommended_movies]

        return JsonResponse({'status': 'success', 'movies': movies_data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# -----------------------------------------------------------------------
# User Profile API
# -----------------------------------------------------------------------

def get_user_profile(request, user_id):
    try:
        user           = get_object_or_404(User, id=user_id)
        movies_watched = user.watch_history.count()
        reviews_count  = user.reviews.count()

        profile_data = {
            'username':       user.username,
            'full_name':      f"{user.first_name} {user.last_name}".strip() or user.username,
            'email':          user.email or 'Email not provided',
            'movies_watched': movies_watched,
            'reviews_count':  reviews_count,
            'joined':         user.date_joined.strftime('%B %Y'),
        }

        return JsonResponse({'status': 'success', 'profile': profile_data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# -----------------------------------------------------------------------
# Video Player
# -----------------------------------------------------------------------

@login_required
def video_player(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id, is_published=True)

    movie.views = F('views') + 1
    movie.save(update_fields=['views'])

    WatchHistory.objects.get_or_create(user=request.user, movie=movie)

    # FIXED: use create (not get_or_create) so every visit to the player page
    # records a fresh watch interaction for recency-based recommendations.
    UserInteraction.objects.create(
        user=request.user,
        movie=movie,
        interaction_type='watch',
        score=2.0,
        created_at=timezone.now()
    )

    return render(request, 'movies/player.html', {'movie': movie})


# -----------------------------------------------------------------------
# Favorites API
# -----------------------------------------------------------------------

@login_required
@require_POST
def toggle_favorite(request):
    try:
        data     = json.loads(request.body)
        movie_id = data.get('movie_id')
        movie    = get_object_or_404(Movie, id=movie_id)

        fav, created = Favorite.objects.get_or_create(user=request.user, movie=movie)
        if not created:
            fav.delete()
            return JsonResponse({'status': 'success', 'action': 'removed'})

        return JsonResponse({'status': 'success', 'action': 'added'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def check_favorite(request, movie_id):
    is_fav = Favorite.objects.filter(user=request.user, movie_id=movie_id).exists()
    return JsonResponse({'is_favorite': is_fav})