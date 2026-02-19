from movies.models import Movie

def all_movies(request):
    """
    Context processor to make all movies available in all templates
    for the search sidebar functionality
    """
    if request.user.is_authenticated:
        movies = Movie.objects.filter(is_published=True).select_related('language').prefetch_related('genres').all()
        return {'all_movies': movies}
    return {'all_movies': []}
