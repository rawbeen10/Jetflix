from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),          
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('search/', views.search_view, name='search'),
    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('watch_history/', views.watch_history_view, name='watch_history'),
    path('edit_profile/', views.edit_profile_view, name='edit_profile'),
    path('', views.home_page, name='home'),
    path('api/search/', views.search_movies_api, name='search_movies_api'),

    
]