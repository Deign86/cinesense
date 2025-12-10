import os
import sys
import random

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinesense_project.settings')
import django
django.setup()

from movies.models import Movie, Rating
from django.contrib.auth.models import User

def create_data():
    print("Creating dummy data...")
    
    # Create movies
    genres = ['Action', 'Drama', 'Comedy', 'Sci-Fi', 'Thriller', 'Romance', 'Horror']
    
    created_count = 0
    for i in range(50):
        year = random.randint(1990, 2024)
        popularity = random.uniform(10.0, 100.0)
        
        # Determine genres
        num_genres = random.randint(1, 3)
        movie_genres = random.sample(genres, num_genres)
        genres_str = ", ".join(movie_genres)
        
        title = f"Dummy Movie {i+1}"
        
        movie, created = Movie.objects.get_or_create(
            title=title,
            defaults={
                'year': year,
                'genres': genres_str,
                'overview': f"This is a dummy overview for movie {i+1}.",
                'popularity': popularity,
                'runtime': random.randint(90, 180)
            }
        )
        if created:
            created_count += 1
            
    print(f"Created {created_count} movies.")
    
    # Check total
    count = Movie.objects.count()
    print(f"Total movies in database: {count}")

if __name__ == "__main__":
    create_data()
