from django.db import models

class Movie(models.Model):
    GENRE_CHOICES = [
        ('Action', 'Action'),
        ('Drama', 'Drama'),
        ('Comedy', 'Comedy'),
        ('Horror', 'Horror'),
        ('Romance', 'Romance'),
        ('Sci-Fi', 'Sci-Fi'),
        ('Thriller', 'Thriller'),
        ('Fantasy', 'Fantasy'),
        ('Adventure', 'Adventure'),
    ]

    title = models.CharField(max_length=255)
    year = models.IntegerField()
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='thumbnails/')
    video = models.FileField(upload_to='movies/')
    genre = models.CharField(max_length=50, choices=GENRE_CHOICES, default='Action')
    cast = models.CharField(max_length=255, help_text='Comma-separated list of main actors', default='Unknown')
    movie_length = models.CharField(max_length=20, help_text='Duration e.g. 2h 30m', default='0h 0m')
    review_stars = models.FloatField(default=0.0, help_text='Average rating out of 5')
    views = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title
