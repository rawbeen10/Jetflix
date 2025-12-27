#!/usr/bin/env python3

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/Users/kushalbhattarai/Projects/Jetflix')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Jetflix.settings')
django.setup()

from django.contrib.auth.models import User
from movies.models import Movie, Review

def test_review_system():
    print("Testing Review System...")
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"Created test user: {user.username}")
    else:
        print(f"Using existing user: {user.username}")
    
    # Get the first movie
    movie = Movie.objects.first()
    if not movie:
        print("No movies found. Please add some movies first.")
        return
    
    print(f"Testing with movie: {movie.title}")
    
    # Create a test review
    review, created = Review.objects.get_or_create(
        user=user,
        movie=movie,
        defaults={
            'rating': 4,
            'review_text': 'This is a test review. Great movie with excellent cinematography!'
        }
    )
    
    if created:
        print(f"Created test review with rating: {review.rating}")
    else:
        print(f"Review already exists with rating: {review.rating}")
    
    # Test the average rating calculation
    print(f"Movie average rating before: {movie.review_stars}")
    movie.update_average_rating()
    print(f"Movie average rating after: {movie.review_stars}")
    
    # Test time since created
    print(f"Review created: {review.time_since_created()}")
    
    print("Review system test completed successfully!")

if __name__ == '__main__':
    test_review_system()