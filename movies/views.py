from django.shortcuts import render
from .models import Movie

def landing_page(request):
    movies = Movie.objects.filter(is_published=True)
    return render(request, 'movies/landing.html', {'movies': movies})

