from django.contrib import admin
from .models import Movie

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'genre', 'is_published')
    list_filter = ('genre', 'is_published')
    search_fields = ('title', 'cast')
