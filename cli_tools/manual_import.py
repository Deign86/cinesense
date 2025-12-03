#!/usr/bin/env python
"""
CineSense CLI Tool - Manual Movie Import
=========================================

Demonstrates:
- User input with input()
- Casting (str to int, float)
- String modification
- If/else conditional logic
- For loops and while loops
- Collections (list, dict)
- f-strings with format modifiers
- Django ORM operations

Usage:
    python cli_tools/manual_import.py

Run from the cinesense_project directory after setting up Django.
"""

import os
import sys

# Add parent directory to path for Django setup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinesense_project.settings')

import django
django.setup()

# Now we can import Django models
from movies.models import Movie, Rating, UserProfile
from django.contrib.auth.models import User


def print_header(title: str) -> None:
    """
    Print a formatted header.
    
    Demonstrates: f-strings, string multiplication
    """
    width = 50
    print("\n" + "=" * width)
    print(f"  {title}")  # f-string
    print("=" * width)


def get_string_input(prompt: str, required: bool = True, default: str = "") -> str:
    """
    Get string input from user.
    
    Demonstrates: input(), while loop, if/else, string modification
    """
    while True:
        # Get input with prompt (f-string)
        if default:
            display_prompt = f"{prompt} [{default}]: "
        else:
            display_prompt = f"{prompt}: "
        
        value = input(display_prompt)  # User input
        
        # String modification: strip whitespace
        value = value.strip()
        
        # If/else: Handle empty input
        if not value:
            if default:
                return default
            elif required:
                print("  This field is required. Please enter a value.")
                continue
            else:
                return ""
        
        return value


def get_int_input(prompt: str, min_val: int = None, max_val: int = None, default: int = None) -> int:
    """
    Get integer input with validation.
    
    Demonstrates: input(), casting (str to int), while loop, if/else
    """
    while True:
        # Build prompt with f-string
        if default is not None:
            display_prompt = f"{prompt} [{default}]: "
        else:
            display_prompt = f"{prompt}: "
        
        value_str = input(display_prompt)
        value_str = value_str.strip()
        
        # If/else: Handle empty input
        if not value_str:
            if default is not None:
                return default
            else:
                print("  Please enter a number.")
                continue
        
        # Casting: string to int
        try:
            value = int(value_str)  # Cast to int
        except ValueError:
            print(f"  '{value_str}' is not a valid number.")
            continue
        
        # Validation with if/else
        if min_val is not None and value < min_val:
            print(f"  Value must be at least {min_val}.")
            continue
        
        if max_val is not None and value > max_val:
            print(f"  Value must be at most {max_val}.")
            continue
        
        return value


def get_float_input(prompt: str, min_val: float = None, max_val: float = None, default: float = None) -> float:
    """
    Get float input with validation.
    
    Demonstrates: input(), casting (str to float), while loop, if/else
    """
    while True:
        # f-string for prompt
        if default is not None:
            display_prompt = f"{prompt} [{default}]: "
        else:
            display_prompt = f"{prompt}: "
        
        value_str = input(display_prompt)
        value_str = value_str.strip()
        
        if not value_str:
            if default is not None:
                return default
            else:
                print("  Please enter a number.")
                continue
        
        # Casting: string to float
        try:
            value = float(value_str)  # Cast to float
        except ValueError:
            print(f"  '{value_str}' is not a valid number.")
            continue
        
        # Validation
        if min_val is not None and value < min_val:
            print(f"  Value must be at least {min_val}.")
            continue
        
        if max_val is not None and value > max_val:
            print(f"  Value must be at most {max_val}.")
            continue
        
        return value


def get_yes_no(prompt: str, default: bool = True) -> bool:
    """
    Get yes/no input.
    
    Demonstrates: input(), string modification (lower), if/else
    """
    default_str = "Y/n" if default else "y/N"
    
    while True:
        value = input(f"{prompt} [{default_str}]: ")
        value = value.strip().lower()  # String modification
        
        if not value:
            return default
        
        # If/else chain
        if value in ('y', 'yes', 'true', '1'):
            return True
        elif value in ('n', 'no', 'false', '0'):
            return False
        else:
            print("  Please enter 'y' or 'n'.")


def get_list_input(prompt: str, separator: str = ",") -> list:
    """
    Get comma-separated list input.
    
    Demonstrates: input(), string modification (split, strip),
                 list comprehension
    """
    value = input(f"{prompt} (separated by '{separator}'): ")
    
    if not value.strip():
        return []
    
    # String split and list comprehension
    items = [
        item.strip()
        for item in value.split(separator)
        if item.strip()  # Filter empty items
    ]
    
    return items


def add_movie() -> None:
    """
    Add a new movie via CLI.
    
    Demonstrates: User input, casting, Django ORM, f-strings
    """
    print_header("Add New Movie")
    
    # Collect movie data using various input functions
    title = get_string_input("Movie title")
    year = get_int_input("Release year", min_val=1888, max_val=2100)
    
    # Get genres as list
    genres_list = get_list_input("Genres", separator=",")
    genres_str = ", ".join([g.title() for g in genres_list])  # String join
    
    overview = get_string_input("Overview/Description", required=False)
    runtime = get_int_input("Runtime in minutes", min_val=1, max_val=1000, default=None) if get_yes_no("Add runtime?") else None
    popularity = get_float_input("Popularity score", min_val=0, max_val=1000, default=0.0)
    
    # Confirm with f-string
    print(f"\n--- Movie Summary ---")
    print(f"Title: {title}")
    print(f"Year: {year}")
    print(f"Genres: {genres_str}")
    print(f"Overview: {overview[:50]}..." if len(overview) > 50 else f"Overview: {overview}")
    print(f"Runtime: {runtime} minutes" if runtime else "Runtime: Not set")
    print(f"Popularity: {popularity:.1f}")  # f-string with format modifier
    
    if get_yes_no("\nSave this movie?"):
        # Django ORM: Create and save
        movie = Movie(
            title=title,
            year=year,
            genres=genres_str,
            overview=overview,
            runtime=runtime,
            popularity=popularity,
        )
        movie.save()
        print(f"\n✅ Movie '{movie}' saved with ID {movie.pk}!")
    else:
        print("\n❌ Movie not saved.")


def add_rating() -> None:
    """
    Add a rating for a movie.
    
    Demonstrates: User input, Django ORM queries, if/else, for loop
    """
    print_header("Add Movie Rating")
    
    # Search for movie
    search = get_string_input("Search for movie title")
    
    # Django ORM: Filter with icontains
    movies = Movie.objects.filter(title__icontains=search)[:10]
    
    # If/else: Check results
    if not movies:
        print(f"\n❌ No movies found matching '{search}'.")
        return
    
    # Display results using for loop
    print(f"\nFound {movies.count()} movie(s):")
    for i, movie in enumerate(movies, 1):  # For loop with enumerate
        print(f"  {i}. {movie}")  # Uses __str__
    
    # Select movie
    selection = get_int_input("\nSelect movie number", min_val=1, max_val=len(movies))
    movie = movies[selection - 1]  # List indexing
    
    # Get or create user
    username = get_string_input("Username", default="cli_user")
    user, created = User.objects.get_or_create(username=username)
    if created:
        print(f"  Created new user: {username}")
    
    # Get rating
    stars = get_float_input("Rating (0.5-5 stars)", min_val=0.5, max_val=5.0)
    tags_list = get_list_input("Tags")
    tags_str = ", ".join(tags_list)
    review = get_string_input("Review text", required=False)
    
    # Check for existing rating
    existing = Rating.objects.filter(user=user, movie=movie).first()
    
    if existing:
        if get_yes_no(f"You already rated this movie ({existing.stars}★). Update?"):
            existing.stars = stars
            existing.tags = tags_str
            existing.review_text = review
            existing.save()
            print(f"\n✅ Rating updated: {existing}")
        else:
            print("\n❌ Rating not updated.")
    else:
        # Create new rating
        rating = Rating.objects.create(
            user=user,
            movie=movie,
            stars=stars,
            tags=tags_str,
            review_text=review,
        )
        print(f"\n✅ Rating saved: {rating}")


def list_movies() -> None:
    """
    List movies with filtering options.
    
    Demonstrates: Django ORM, for loop, if/else, lambdas
    """
    print_header("List Movies")
    
    # Filter options
    genre_filter = get_string_input("Filter by genre (or press Enter for all)", required=False)
    min_year = get_int_input("Minimum year", min_val=1888, max_val=2100, default=1900)
    
    # Build queryset
    movies = Movie.objects.all()
    
    if genre_filter:
        movies = movies.filter(genres__icontains=genre_filter)
    
    movies = movies.filter(year__gte=min_year)
    
    # Sort options - dict of sort keys
    sort_options = {
        '1': ('title', 'Title A-Z'),
        '2': ('-title', 'Title Z-A'),
        '3': ('year', 'Year (oldest first)'),
        '4': ('-year', 'Year (newest first)'),
        '5': ('-popularity', 'Popularity'),
    }
    
    print("\nSort by:")
    for key, (_, label) in sort_options.items():
        print(f"  {key}. {label}")
    
    sort_choice = get_string_input("Select sort option", default="1")
    sort_field, _ = sort_options.get(sort_choice, ('title', 'Title A-Z'))
    
    movies = movies.order_by(sort_field)[:20]  # Limit to 20
    
    # Display results
    print(f"\n📽️ Movies ({movies.count()} results):")
    print("-" * 60)
    
    # For loop to display movies
    for i, movie in enumerate(movies, 1):
        avg = movie.average_rating
        rating_str = f"★{avg:.1f}" if avg > 0 else "No ratings"
        
        # f-string with multiple format modifiers
        print(f"{i:3d}. {movie.title[:35]:35s} ({movie.year}) {rating_str:>10s}")
    
    print("-" * 60)


def show_statistics() -> None:
    """
    Show movie statistics.
    
    Demonstrates: Django ORM aggregation, collections, for loop
    """
    print_header("Statistics")
    
    from django.db.models import Avg, Count
    
    # Basic counts
    movie_count = Movie.objects.count()
    rating_count = Rating.objects.count()
    user_count = User.objects.count()
    
    print(f"\n📊 Database Statistics:")
    print(f"  Movies: {movie_count}")
    print(f"  Ratings: {rating_count}")
    print(f"  Users: {user_count}")
    
    # Genre statistics - using dict
    genre_counts = {}  # dict: genre -> count
    
    # For loop over all movies
    for movie in Movie.objects.all():
        genres = movie.get_genres_list()  # list
        for genre in genres:
            if genre in genre_counts:
                genre_counts[genre] += 1
            else:
                genre_counts[genre] = 1
    
    # Sort using lambda
    sorted_genres = sorted(
        genre_counts.items(),
        key=lambda x: x[1],  # Lambda: sort by count
        reverse=True
    )[:10]
    
    print(f"\n🎭 Top Genres:")
    for genre, count in sorted_genres:
        print(f"  {genre}: {count} movies")
    
    # Top rated movies
    top_rated = Movie.objects.annotate(
        avg_rating=Avg('ratings__stars'),
        num_ratings=Count('ratings')
    ).filter(rating_count__gte=1).order_by('-avg_rating')[:5]
    
    if top_rated:
        print(f"\n⭐ Top Rated Movies:")
        for movie in top_rated:
            print(f"  {movie.title}: {movie.avg_rating:.2f}★ ({movie.rating_count} ratings)")


def import_sample_data() -> None:
    """
    Import sample movie data.
    
    Demonstrates: Collections (list of dicts), for loop, Django ORM bulk operations
    """
    print_header("Import Sample Data")
    
    # Sample movies - list of dicts
    sample_movies = [
        {
            'title': 'The Shawshank Redemption',
            'year': 1994,
            'genres': 'Drama',
            'popularity': 95.5,
            'overview': 'Two imprisoned men bond over years, finding solace and redemption.',
        },
        {
            'title': 'The Dark Knight',
            'year': 2008,
            'genres': 'Action, Drama, Crime',
            'popularity': 92.3,
            'overview': 'Batman faces the Joker in a battle for Gotham City.',
        },
        {
            'title': 'Inception',
            'year': 2010,
            'genres': 'Action, Sci-Fi, Thriller',
            'popularity': 88.7,
            'overview': 'A thief who enters dreams to steal secrets must plant an idea instead.',
        },
        {
            'title': 'Pulp Fiction',
            'year': 1994,
            'genres': 'Crime, Drama',
            'popularity': 86.2,
            'overview': 'Intertwined stories of criminals in Los Angeles.',
        },
        {
            'title': 'The Matrix',
            'year': 1999,
            'genres': 'Action, Sci-Fi',
            'popularity': 89.1,
            'overview': 'A hacker discovers reality is a simulation.',
        },
        {
            'title': 'Forrest Gump',
            'year': 1994,
            'genres': 'Drama, Romance',
            'popularity': 87.4,
            'overview': 'The story of a simple man who witnesses historic events.',
        },
        {
            'title': 'The Lord of the Rings: The Fellowship of the Ring',
            'year': 2001,
            'genres': 'Fantasy, Adventure',
            'popularity': 91.0,
            'overview': 'A hobbit embarks on a quest to destroy a powerful ring.',
        },
        {
            'title': 'Interstellar',
            'year': 2014,
            'genres': 'Sci-Fi, Drama, Adventure',
            'popularity': 85.5,
            'overview': 'Astronauts travel through a wormhole in search of a new home.',
        },
        {
            'title': 'The Godfather',
            'year': 1972,
            'genres': 'Crime, Drama',
            'popularity': 93.2,
            'overview': 'The aging patriarch of a crime dynasty transfers control.',
        },
        {
            'title': 'Fight Club',
            'year': 1999,
            'genres': 'Drama, Thriller',
            'popularity': 84.8,
            'overview': 'An insomniac office worker forms an underground fight club.',
        },
    ]
    
    if not get_yes_no(f"Import {len(sample_movies)} sample movies?"):
        print("❌ Import cancelled.")
        return
    
    imported = 0
    skipped = 0
    
    # For loop over sample data
    for movie_data in sample_movies:
        # Check if already exists
        exists = Movie.objects.filter(
            title=movie_data['title'],
            year=movie_data['year']
        ).exists()
        
        if exists:
            skipped += 1
            print(f"  ⏭️ Skipped (exists): {movie_data['title']}")
        else:
            # Create movie using dict unpacking
            Movie.objects.create(**movie_data)
            imported += 1
            print(f"  ✅ Imported: {movie_data['title']}")
    
    # Summary with f-strings
    print(f"\n📊 Import Summary:")
    print(f"  Imported: {imported}")
    print(f"  Skipped: {skipped}")


def main_menu() -> None:
    """
    Main menu loop.
    
    Demonstrates: While loop, if/elif/else, dict for menu options
    """
    # Menu options - dict
    menu_options = {
        '1': ('Add Movie', add_movie),
        '2': ('Add Rating', add_rating),
        '3': ('List Movies', list_movies),
        '4': ('Show Statistics', show_statistics),
        '5': ('Import Sample Data', import_sample_data),
        '0': ('Exit', None),
    }
    
    # While loop for menu
    while True:
        print_header("CineSense CLI Tools")
        
        # For loop to display menu
        for key, (label, _) in menu_options.items():
            print(f"  {key}. {label}")
        
        choice = get_string_input("\nSelect option", default="0")
        
        # If/elif/else for menu handling
        if choice in menu_options:
            label, func = menu_options[choice]
            
            if func is None:
                print("\n👋 Goodbye!")
                break
            else:
                func()  # Call selected function
        else:
            print(f"\n❌ Invalid option: {choice}")
        
        input("\nPress Enter to continue...")


if __name__ == '__main__':
    main_menu()
