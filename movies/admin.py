from django.contrib import admin
from .models import Movie, Watchlist

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'genre', 'is_published', 'views')
    list_filter = ('genre', 'is_published', 'year')
    search_fields = ('title', 'cast')

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'added_on')
    list_filter = ('added_on',)
    search_fields = ('user__username', 'movie__title')