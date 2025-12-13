from django.urls import path
from . import views
from .views import all_movies

urlpatterns = [
    path('login/', views.admin_login, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('add-movie/', views.add_movie, name='add_movie'),
     path('movies/', all_movies, name='admin-all-movies'),

]
