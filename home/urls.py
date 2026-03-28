from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login_alt'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.home_page, name='home'),
    path('search/', views.search_view, name='search'),
    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('profile/', views.profile_view, name='profile'),
    path('watch_history/', views.watch_history_view, name='watch_history'),
    path('edit_profile/', views.edit_profile_view, name='edit_profile'),
    path('media/<path:path>', views.video_stream, name='video_stream'),
]
