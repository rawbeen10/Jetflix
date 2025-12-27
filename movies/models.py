from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Count, Q
from django.utils import timezone
from collections import defaultdict
import math

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
    
    def update_average_rating(self):
        """Update the average rating based on all reviews"""
        avg_rating = self.reviews.aggregate(Avg('rating'))['rating__avg']
        self.review_stars = avg_rating if avg_rating else 0.0
        self.save(update_fields=['review_stars'])
    
    def get_similar_movies(self, limit=6):
        """Get movies similar to this one using item-based collaborative filtering"""
        # Get users who interacted with this movie
        user_ids = list(self.interactions.values_list('user_id', flat=True).distinct())
        
        if not user_ids:
            # Fallback to genre-based recommendations
            return Movie.objects.filter(
                genres__in=self.genres.all(),
                is_published=True
            ).exclude(id=self.id).distinct()[:limit]
        
        # Find movies these users also interacted with
        similar_movies = Movie.objects.filter(
            interactions__user_id__in=user_ids,
            is_published=True
        ).exclude(id=self.id).annotate(
            interaction_count=Count('interactions__user_id', distinct=True)
        ).order_by('-interaction_count', '-review_stars')[:limit]
        
        return similar_movies
    
    @classmethod
    def get_recommendations_for_user(cls, user, limit=6):
        """Get personalized recommendations for a user"""
        # Get user's interaction history
        user_movies = list(user.interactions.values_list('movie_id', flat=True).distinct())
        
        if not user_movies:
            # Cold start: return popular movies
            return cls.objects.filter(
                is_published=True
            ).order_by('-review_stars', '-views')[:limit]
        
        # Find similar users based on common movie interactions
        similar_users = User.objects.filter(
            interactions__movie_id__in=user_movies
        ).exclude(id=user.id).annotate(
            common_movies=Count('interactions__movie_id', 
                              filter=Q(interactions__movie_id__in=user_movies))
        ).filter(common_movies__gte=2).order_by('-common_movies')[:10]
        
        if not similar_users:
            # Fallback to genre-based recommendations
            user_genres = cls.objects.filter(
                id__in=user_movies
            ).values_list('genres', flat=True)
            
            return cls.objects.filter(
                genres__in=user_genres,
                is_published=True
            ).exclude(id__in=user_movies).distinct().order_by('-review_stars')[:limit]
        
        # Get movies liked by similar users
        recommended_movies = cls.objects.filter(
            interactions__user__in=similar_users,
            is_published=True
        ).exclude(id__in=user_movies).annotate(
            recommendation_score=Count('interactions__user', distinct=True)
        ).order_by('-recommendation_score', '-review_stars')[:limit]
        
        return recommended_movies

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
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.movie.update_average_rating()
    
    def delete(self, *args, **kwargs):
        movie = self.movie
        super().delete(*args, **kwargs)
        movie.update_average_rating()
    
    def time_since_created(self):
        """Return human-readable time since creation"""
        now = timezone.now()
        diff = now - self.created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} min{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"

class WatchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_history')
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    watched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-watched_at']
        verbose_name_plural = 'Watch Histories'
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"

class UserInteraction(models.Model):
    """Track user interactions for collaborative filtering"""
    INTERACTION_TYPES = [
        ('watch', 'Watched'),
        ('review', 'Reviewed'),
        ('watchlist', 'Added to Watchlist'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactions')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    score = models.FloatField(default=1.0)  # Weight of interaction
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'movie', 'interaction_type')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.movie.title} ({self.interaction_type})"