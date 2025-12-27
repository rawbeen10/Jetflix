from django.contrib import admin
from .models import Movie, Watchlist, Review, Language, Genre, WatchHistory, UserInteraction

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'year', 'get_genres', 'language', 'review_stars', 'views', 'is_published']
    list_filter = ['is_published', 'year', 'language', 'genres']
    search_fields = ['title', 'cast', 'description']
    filter_horizontal = ['genres']  # Nice UI for ManyToMany field
    
    def get_genres(self, obj):
        """Display genres as comma-separated list in admin"""
        return obj.get_genres_display()
    get_genres.short_description = 'Genres'

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'added_on']
    list_filter = ['added_on']
    search_fields = ['user__username', 'movie__title']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'movie__title', 'review_text']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'watched_at']
    list_filter = ['watched_at']
    search_fields = ['user__username', 'movie__title']
    readonly_fields = ['watched_at']

@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'interaction_type', 'score', 'created_at']
    list_filter = ['interaction_type', 'created_at']
    search_fields = ['user__username', 'movie__title']
    readonly_fields = ['created_at']