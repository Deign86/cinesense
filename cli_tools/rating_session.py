#!/usr/bin/env python
"""
CineSense CLI Tool - Interactive Rating Session
===============================================

Demonstrates:
- User input with input()
- Casting between types
- While loops
- If/else conditions
- Collections (list, dict, set)
- Django ORM operations
- f-strings

Usage:
    python cli_tools/rating_session.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinesense_project.settings')

import django
django.setup()

from movies.models import Movie, Rating
from django.contrib.auth.models import User
import random


def get_input(prompt: str, input_type: type = str, default=None):
    """
    Universal input function with type casting.
    
    Demonstrates: input(), casting, if/else, try/except
    """
    while True:
        # Build prompt string with f-string
        if default is not None:
            full_prompt = f"{prompt} [{default}]: "
        else:
            full_prompt = f"{prompt}: "
        
        value = input(full_prompt).strip()  # String modification
        
        # Handle empty input
        if not value:
            if default is not None:
                return default
            continue
        
        # Type casting based on input_type
        try:
            if input_type == int:
                return int(value)  # Cast to int
            elif input_type == float:
                return float(value)  # Cast to float
            elif input_type == bool:
                return value.lower() in ('y', 'yes', 'true', '1')
            else:
                return str(value)  # Cast to str
        except ValueError:
            print(f"  Invalid input. Expected {input_type.__name__}.")


def rate_random_movies(user: User, count: int = 5):
    """
    Rate random movies in a session.
    
    Demonstrates: While loop, for loop, set operations, Django ORM
    """
    # Get user's already-rated movie IDs as a set
    rated_ids = set(
        Rating.objects.filter(user=user).values_list('movie_id', flat=True)
    )
    
    # Get unrated movies
    unrated = Movie.objects.exclude(pk__in=rated_ids)
    unrated_list = list(unrated)  # Cast queryset to list
    
    if len(unrated_list) < count:
        print(f"Only {len(unrated_list)} unrated movies available.")
        count = len(unrated_list)
    
    if count == 0:
        print("You've rated all available movies!")
        return
    
    # Randomly select movies
    random.shuffle(unrated_list)
    movies_to_rate = unrated_list[:count]
    
    ratings_given = []  # List to track ratings
    
    print(f"\n🎬 Rating Session: {count} movies")
    print("=" * 50)
    
    # For loop over selected movies
    for i, movie in enumerate(movies_to_rate, 1):
        print(f"\n[{i}/{count}] {movie.title} ({movie.year})")
        print(f"Genres: {movie.genres}")
        if movie.overview:
            print(f"Overview: {movie.overview[:100]}...")
        
        # Options
        print("\nOptions: rate (0.5-5), skip (s), quit (q)")
        
        # While loop for valid input
        while True:
            choice = input("Your choice: ").strip().lower()
            
            if choice == 'q':
                print("\n👋 Session ended.")
                return
            elif choice == 's':
                print("⏭️ Skipped")
                break
            else:
                # Try to cast to float
                try:
                    stars = float(choice)
                    if 0.5 <= stars <= 5.0:
                        # Create rating
                        rating = Rating.objects.create(
                            user=user,
                            movie=movie,
                            stars=stars,
                        )
                        ratings_given.append((movie.title, stars))
                        print(f"✅ Rated {stars:.1f}★")  # f-string with format
                        break
                    else:
                        print("Rating must be between 0.5 and 5.0")
                except ValueError:
                    print("Invalid input. Enter a number (0.5-5), 's' to skip, or 'q' to quit.")
    
    # Session summary
    print("\n" + "=" * 50)
    print("📊 Session Summary")
    print("=" * 50)
    
    if ratings_given:
        total = sum(r[1] for r in ratings_given)
        avg = total / len(ratings_given)
        
        print(f"Movies rated: {len(ratings_given)}")
        print(f"Average rating: {avg:.2f}★")
        print("\nRatings given:")
        
        for title, stars in ratings_given:
            print(f"  • {title}: {stars:.1f}★")
    else:
        print("No ratings given.")


def main():
    """
    Main entry point.
    
    Demonstrates: User input, Django ORM, if/else
    """
    print("\n🎬 CineSense Rating Session")
    print("=" * 40)
    
    # Get or create user
    username = get_input("Enter username", str, "session_user")
    user, created = User.objects.get_or_create(username=username)
    
    if created:
        print(f"✨ Welcome, new user {username}!")
    else:
        rating_count = Rating.objects.filter(user=user).count()
        print(f"👋 Welcome back, {username}! You have {rating_count} ratings.")
    
    # Get number of movies to rate
    count = get_input("How many movies to rate?", int, 5)
    
    # Start rating session
    rate_random_movies(user, count)


if __name__ == '__main__':
    main()
