from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    # path('trending/', views.trending_movies, name='trending'),
    path('watchlist/', views.watchlist_page, name='watchlist'),
    path('api/watchlist/add/', views.add_to_watchlist, name='add_to_watchlist'),
    path('api/watchlist/remove/', views.remove_from_watchlist, name='remove_from_watchlist'),
    path('api/increment-view/', views.increment_view, name='increment_view'),
]