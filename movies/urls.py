from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('watchlist/', views.watchlist_page, name='watchlist'),
    path('player/<int:movie_id>/', views.video_player, name='video_player'),
    path('api/watchlist/add/', views.add_to_watchlist, name='add_to_watchlist'),
    path('api/watchlist/remove/', views.remove_from_watchlist, name='remove_from_watchlist'),
    path('api/increment-view/', views.increment_view, name='increment_view'),
    # Review endpoints
    path('api/reviews/<int:movie_id>/', views.get_reviews, name='get_reviews'),
    path('api/reviews/add/', views.add_review, name='add_review'),
    path('api/reviews/edit/<int:review_id>/', views.edit_review, name='edit_review'),
    path('api/reviews/delete/<int:review_id>/', views.delete_review, name='delete_review'),
    # Recommendation endpoints
    path('api/recommendations/similar/<int:movie_id>/', views.get_similar_movies, name='get_similar_movies'),
    path('api/recommendations/user/', views.get_user_recommendations, name='get_user_recommendations'),
    path('api/user/<int:user_id>/', views.get_user_profile, name='get_user_profile'),
]