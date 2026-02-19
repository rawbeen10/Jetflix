from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Movie

# Custom User admin for adminpanel
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering = ['-id']

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'year', 'genre', 'cast', 'movie_length', 'review_stars', 'views', 'is_published']
    list_filter = ['is_published', 'year', 'genre']
    search_fields = ['title', 'cast', 'description']
    readonly_fields = ['views']
    list_editable = ['is_published', 'review_stars']
    ordering = ['-id']

# Register User admin only if not already registered
if not admin.site.is_registered(User):
    admin.site.register(User, CustomUserAdmin)
