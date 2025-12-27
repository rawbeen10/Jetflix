from django.urls import path
from django.shortcuts import redirect
from . import views
from .views import all_movies

def admin_root_redirect(request):
    return redirect('admin_login')

urlpatterns = [
    path('', admin_root_redirect, name='admin_root'),
    path('login/', views.admin_login, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('add-movie/', views.add_movie, name='add_movie'),
    path('movies/', all_movies, name='admin-all-movies'),
    path('movies/edit/<int:movie_id>/', views.edit_movie, name='edit_movie'),
    path('movies/delete/<int:movie_id>/', views.delete_movie, name='delete_movie'),
    path('reviews/', views.manage_reviews, name='manage_reviews'),
    path('reviews/delete/<int:review_id>/', views.delete_review_admin, name='delete_review_admin'),
    path('users/', views.manage_users, name='manage_users'),
    path('users/<int:user_id>/', views.user_profile, name='user_profile'),
]