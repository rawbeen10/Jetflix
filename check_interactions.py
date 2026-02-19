#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Jetflix.settings')
django.setup()

from movies.models import UserInteraction, Movie
from django.contrib.auth.models import User

print("=== UserInteraction Check ===")
print(f"Total interactions: {UserInteraction.objects.count()}")
print(f"\nBy type:")
for t in ['watch', 'review', 'watchlist']:
    count = UserInteraction.objects.filter(interaction_type=t).count()
    print(f"  {t}: {count}")

print(f"\n=== User Check ===")
users = User.objects.all()
for user in users:
    interactions = UserInteraction.objects.filter(user=user).count()
    print(f"User: {user.username} - Interactions: {interactions}")

print(f"\n=== Movie Check ===")
print(f"Total movies: {Movie.objects.count()}")
print(f"Published movies: {Movie.objects.filter(is_published=True).count()}")
