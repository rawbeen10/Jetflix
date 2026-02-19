#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Jetflix.settings')
django.setup()

from movies.models import Movie
from django.contrib.auth.models import User

print("=== Testing Recommendations ===\n")

# Test with a user who has interactions
user = User.objects.get(username='rabin')  # Has 8 interactions
print(f"Testing for user: {user.username}")
print(f"User interactions: {user.interactions.count()}")

# Get recommendations
recommendations = Movie.get_recommendations_for_user(user, limit=12)
print(f"\nRecommendations returned: {len(recommendations)}")

if recommendations:
    print("\nRecommended movies:")
    for i, movie in enumerate(recommendations, 1):
        print(f"  {i}. {movie.title} (Rating: {movie.review_stars}, Views: {movie.views})")
else:
    print("No recommendations returned!")
    
# Check what movies the user has interacted with
user_movies = list(user.interactions.values_list('movie_id', flat=True).distinct())
print(f"\nUser has interacted with {len(user_movies)} movies:")
for movie_id in user_movies:
    movie = Movie.objects.get(id=movie_id)
    print(f"  - {movie.title}")
