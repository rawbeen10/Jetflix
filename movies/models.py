from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Language(models.Model):
    """Language model for movies"""
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True, help_text='ISO 639-1 code (e.g., en, es, fr)')
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Genre(models.Model):
    """Genre model for movies - enables multiple genres per movie"""
    name = models.CharField(max_length=50, unique=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Movie(models.Model):
    title = models.CharField(max_length=255)
    year = models.IntegerField()
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='thumbnails/')
    video = models.FileField(upload_to='movies/')
    genres = models.ManyToManyField(Genre, related_name='movies', help_text='Select multiple genres')
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True, related_name='movies')
    cast = models.CharField(max_length=255, default='Unknown', help_text='Comma-separated list of main actors')
    movie_length = models.CharField(max_length=20, default='Unknown', help_text='Duration e.g. 2h 30m')
    review_stars = models.FloatField(default=0.0, help_text='Average rating out of 5')
    views = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
    
    def get_genres_display(self):
        """Returns comma-separated list of genres"""
        return ", ".join([genre.name for genre in self.genres.all()])

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='watchlisted_by')
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-added_on']
    
    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"
        
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rating from 1 to 5 stars'
    )
    review_text = models.TextField(help_text='Your review')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-created_at']

class WatchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_history')
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    watched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-watched_at']
        verbose_name_plural = 'Watch Histories'


    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"