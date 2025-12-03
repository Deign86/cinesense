"""
CineSense Models
================

Demonstrates:
- Classes and objects
- __init__ and __str__ methods  
- Methods and self
- Inheritance (TimestampedModel abstract base class)
- Django ORM (database models)
- f-strings with format modifiers
- Collections (list, set operations)
- String modification and parsing
- Properties
- Casting (int, float, str)
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from typing import List, Set


class TimestampedModel(models.Model):
    """
    Abstract base class providing timestamp fields.
    
    Demonstrates: Inheritance (abstract base class pattern)
    All other models inherit from this class.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True  # This makes it an abstract base class
    
    def get_age_days(self) -> int:
        """
        Calculate age in days since creation.
        
        Demonstrates: Methods with self, casting to int
        """
        from django.utils import timezone
        delta = timezone.now() - self.created_at
        return int(delta.days)  # Casting: float to int
    
    def __str__(self) -> str:
        """Base __str__ - subclasses should override"""
        return f"{self.__class__.__name__} (id={self.pk})"


class UserProfile(TimestampedModel):
    """
    Extended user profile for CineSense.
    
    Demonstrates: Inheritance from TimestampedModel
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    favorite_genres = models.CharField(max_length=500, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    
    def __str__(self) -> str:
        """
        Demonstrates: f-strings with self reference
        """
        return f"Profile: {self.user.username}"
    
    def get_favorite_genres_list(self) -> List[str]:
        """
        Parse comma-separated genres into a list.
        
        Demonstrates: String modification (split, strip), 
                     Collections (list), List comprehension
        """
        if not self.favorite_genres:
            return []
        # String ops: split by comma, strip whitespace
        genres = self.favorite_genres.split(',')
        # List comprehension with string methods
        return [genre.strip().title() for genre in genres if genre.strip()]
    
    def set_favorite_genres(self, genres: List[str]) -> None:
        """
        Set genres from a list.
        
        Demonstrates: Collections (list), string join
        """
        # String modification: join list into comma-separated string
        self.favorite_genres = ', '.join(genres)
        self.save()
    
    def get_genre_set(self) -> Set[str]:
        """
        Get genres as a set for set operations.
        
        Demonstrates: Collections (set), casting list to set
        """
        return set(self.get_favorite_genres_list())
    
    @property
    def rating_count(self) -> int:
        """
        Count of ratings by this user.
        
        Demonstrates: Property decorator, Django ORM query
        """
        return Rating.objects.filter(user=self.user).count()


class Movie(TimestampedModel):
    """
    Movie model with full IMDB data capabilities.
    
    Demonstrates: Inheritance, __str__, string operations,
                 collections (list/set), f-strings with format modifiers
    """
    # Basic Info
    title = models.CharField(max_length=255)
    year = models.IntegerField(
        validators=[MinValueValidator(1888), MaxValueValidator(2100)]
    )
    genres = models.CharField(max_length=500, default='')
    overview = models.TextField(blank=True, default='')  # Plot
    poster_path = models.CharField(max_length=500, blank=True, default='')
    runtime = models.IntegerField(null=True, blank=True)  # in minutes
    
    # IMDB Identifiers
    imdb_id = models.CharField(max_length=20, blank=True, default='', db_index=True)
    tmdb_id = models.IntegerField(null=True, blank=True, unique=True)
    
    # Ratings
    imdb_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    imdb_votes = models.CharField(max_length=50, blank=True, default='')
    metascore = models.IntegerField(null=True, blank=True)
    rotten_tomatoes = models.CharField(max_length=10, blank=True, default='')
    
    # Cast & Crew
    director = models.CharField(max_length=500, blank=True, default='')
    writer = models.CharField(max_length=500, blank=True, default='')
    actors = models.CharField(max_length=1000, blank=True, default='')
    
    # Production Info
    rated = models.CharField(max_length=20, blank=True, default='')  # PG, R, etc.
    released = models.CharField(max_length=50, blank=True, default='')
    language = models.CharField(max_length=200, blank=True, default='')
    country = models.CharField(max_length=200, blank=True, default='')
    awards = models.TextField(blank=True, default='')
    
    # Box Office
    box_office = models.CharField(max_length=50, blank=True, default='')
    production = models.CharField(max_length=200, blank=True, default='')
    
    # Internal
    popularity = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-popularity', '-imdb_rating', 'title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['year']),
            models.Index(fields=['tmdb_id']),
            models.Index(fields=['imdb_id']),
            models.Index(fields=['imdb_rating']),
        ]
    
    def __str__(self) -> str:
        """
        Demonstrates: f-strings with format modifiers
        Format: "Movie Title (Year) ★ 4.5"
        """
        avg_rating = self.average_rating
        if avg_rating:
            # f-string with format modifier: .1f for 1 decimal place
            return f"{self.title} ({self.year}) ★ {avg_rating:.1f}"
        return f"{self.title} ({self.year})"
    
    def get_genres_list(self) -> List[str]:
        """
        Parse genres string into list.
        
        Demonstrates: String modification, list comprehension, 
                     conditional logic in comprehension
        """
        if not self.genres:
            return []
        # String split and strip, filtering empty strings
        return [g.strip().title() for g in self.genres.split(',') if g.strip()]
    
    def get_genres_set(self) -> Set[str]:
        """
        Get genres as a set for efficient lookups.
        
        Demonstrates: Casting list to set
        """
        return set(self.get_genres_list())
    
    def set_genres(self, genre_list: List[str]) -> None:
        """
        Set genres from a list.
        
        Demonstrates: String join, list processing
        """
        # Normalize: strip and title case each genre
        normalized = [g.strip().title() for g in genre_list]
        self.genres = ', '.join(normalized)
    
    def has_genre(self, genre: str) -> bool:
        """
        Check if movie has a specific genre.
        
        Demonstrates: String modification (lower), set membership
        """
        genre_set = {g.lower() for g in self.get_genres_list()}
        return genre.lower().strip() in genre_set
    
    @property
    def average_rating(self) -> float:
        """
        Calculate average rating for this movie.
        
        Demonstrates: Django ORM aggregation, property, casting
        """
        from django.db.models import Avg
        result = self.ratings.aggregate(avg=Avg('stars'))
        avg = result.get('avg')
        return float(avg) if avg else 0.0  # Casting: Decimal/None to float
    
    @property
    def rating_count(self) -> int:
        """
        Demonstrates: Property, ORM count
        """
        return self.ratings.count()
    
    @property
    def imdb_url(self) -> str:
        """Get the IMDB URL for this movie."""
        if self.imdb_id:
            return f"https://www.imdb.com/title/{self.imdb_id}/"
        return ""
    
    @property
    def letterboxd_url(self) -> str:
        """Get the Letterboxd URL for this movie."""
        slug = self.title.lower().replace(' ', '-').replace("'", "").replace(":", "")
        return f"https://letterboxd.com/film/{slug}-{self.year}/"
    
    def get_directors_list(self) -> List[str]:
        """Parse directors string into list."""
        if not self.director:
            return []
        return [d.strip() for d in self.director.split(',') if d.strip()]
    
    def get_actors_list(self) -> List[str]:
        """Parse actors string into list."""
        if not self.actors:
            return []
        return [a.strip() for a in self.actors.split(',') if a.strip()]
    
    def get_countries_list(self) -> List[str]:
        """Parse countries string into list."""
        if not self.country:
            return []
        return [c.strip() for c in self.country.split(',') if c.strip()]
    
    def get_languages_list(self) -> List[str]:
        """Parse languages string into list."""
        if not self.language:
            return []
        return [l.strip() for l in self.language.split(',') if l.strip()]
    
    def get_display_runtime(self) -> str:
        """
        Format runtime as hours and minutes.
        
        Demonstrates: Integer division, modulo, f-strings, if/else
        """
        if not self.runtime:
            return "Runtime unknown"
        
        hours = self.runtime // 60  # Integer division
        minutes = self.runtime % 60  # Modulo
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def get_similar_by_genre(self, limit: int = 5):
        """
        Find similar movies by genre overlap.
        
        Demonstrates: For loop, if/else, collections (set, dict),
                     lambda for sorting, Django ORM
        """
        my_genres = self.get_genres_set()
        if not my_genres:
            return Movie.objects.none()
        
        # Get all other movies
        candidates = Movie.objects.exclude(pk=self.pk)
        
        # Calculate genre overlap scores using dict
        scores = {}  # dict: movie_id -> overlap_count
        
        for movie in candidates:
            other_genres = movie.get_genres_set()
            # Set intersection to find common genres
            overlap = my_genres & other_genres  # Set intersection
            if overlap:
                scores[movie.pk] = len(overlap)
        
        # Sort by overlap score using lambda
        sorted_ids = sorted(
            scores.keys(),
            key=lambda pk: scores[pk],  # Lambda function
            reverse=True
        )[:limit]
        
        # Return movies in sorted order
        if not sorted_ids:
            return Movie.objects.none()
        
        # Preserve order using Case/When
        from django.db.models import Case, When
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(sorted_ids)])
        return Movie.objects.filter(pk__in=sorted_ids).order_by(preserved)
    
    @classmethod
    def from_tmdb_json(cls, data: dict) -> 'Movie':
        """
        Create a Movie instance from TMDB JSON data.
        
        This is a factory method for creating Movie objects from the
        TMDB bulk dataset. Use with bulk_create() for best performance.
        
        Args:
            data: Dict with TMDB movie data (id, title, release_date, etc.)
            
        Returns:
            Movie instance (not saved to database)
            
        Example:
            movies = [Movie.from_tmdb_json(d) for d in tmdb_data]
            Movie.objects.bulk_create(movies, ignore_conflicts=True)
        """
        from movies.services.tmdb_parser import TMDBParser
        
        fields = TMDBParser.movie_to_django_fields(data)
        if not fields:
            raise ValueError(f"Invalid movie data: {data}")
        
        return cls(**fields)


class Rating(TimestampedModel):
    """
    User rating for a movie.
    
    Demonstrates: Inheritance, __str__, f-strings, 
                 string parsing, Django ORM relationships
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    stars = models.FloatField(
        validators=[MinValueValidator(0.5), MaxValueValidator(5.0)]
    )
    # Tags as comma-separated string
    tags = models.CharField(max_length=500, blank=True, default='')
    review_text = models.TextField(blank=True, default='')
    
    class Meta:
        unique_together = ['user', 'movie']  # One rating per user per movie
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        """
        Demonstrates: f-strings with format modifiers, nested attribute access
        """
        # f-string with .1f format for rating precision
        return f"{self.user.username} rated '{self.movie.title}': {self.stars:.1f}★"
    
    def get_tags_list(self) -> List[str]:
        """
        Parse tags string into list.
        
        Demonstrates: String modification, list comprehension
        """
        if not self.tags:
            return []
        # Split, strip, and lowercase for consistency
        return [tag.strip().lower() for tag in self.tags.split(',') if tag.strip()]
    
    def get_tags_set(self) -> Set[str]:
        """
        Get tags as a set.
        
        Demonstrates: Set creation from list
        """
        return set(self.get_tags_list())
    
    def set_tags(self, tag_list: List[str]) -> None:
        """
        Set tags from a list.
        
        Demonstrates: String join, list processing
        """
        normalized = [tag.strip().lower() for tag in tag_list if tag.strip()]
        self.tags = ', '.join(normalized)
    
    def add_tag(self, tag: str) -> None:
        """
        Add a single tag.
        
        Demonstrates: If/else, string operations, set operations
        """
        tag = tag.strip().lower()
        if not tag:
            return
        
        current_tags = self.get_tags_set()
        if tag not in current_tags:
            current_tags.add(tag)  # Set add operation
            self.tags = ', '.join(sorted(current_tags))
            self.save()
    
    def get_star_display(self) -> str:
        """
        Get visual star display.
        
        Demonstrates: Casting (float to int), string multiplication,
                     if/else, f-strings
        """
        full_stars = int(self.stars)  # Casting: float to int
        half_star = (self.stars - full_stars) >= 0.5
        
        display = '★' * full_stars  # String multiplication
        if half_star:
            display += '½'
        
        # Pad with empty stars to show rating out of 5
        remaining = 5 - full_stars - (1 if half_star else 0)
        display += '☆' * remaining
        
        return display


class WatchEvent(TimestampedModel):
    """
    Record of when a user watched a movie.
    
    Demonstrates: Inheritance, methods, __str__
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_events')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='watch_events')
    watched_at = models.DateTimeField()
    completed = models.BooleanField(default=True)
    watch_duration = models.IntegerField(null=True, blank=True)  # in minutes
    
    class Meta:
        ordering = ['-watched_at']
    
    def __str__(self) -> str:
        """
        Demonstrates: f-strings, strftime formatting
        """
        date_str = self.watched_at.strftime('%Y-%m-%d')
        return f"{self.user.username} watched '{self.movie.title}' on {date_str}"
    
    def get_completion_percentage(self) -> float:
        """
        Calculate completion percentage.
        
        Demonstrates: If/else, casting, arithmetic
        """
        if not self.watch_duration or not self.movie.runtime:
            return 100.0 if self.completed else 0.0
        
        percentage = (self.watch_duration / self.movie.runtime) * 100
        return min(float(percentage), 100.0)  # Casting and cap at 100%
    
    def get_watch_time_display(self) -> str:
        """
        Demonstrates: Integer division, modulo, f-strings
        """
        if not self.watch_duration:
            return "Unknown"
        
        hours = self.watch_duration // 60
        minutes = self.watch_duration % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


# ==============================================================
# Custom Iterator Example
# ==============================================================

class MovieIterator:
    """
    Custom iterator for movies.
    
    Demonstrates: Custom iterators with __iter__ and __next__,
                 classes, __init__, methods with self
    """
    
    def __init__(self, queryset, batch_size: int = 10):
        """
        Demonstrates: __init__ method, self, type hints
        """
        self.queryset = queryset
        self.batch_size = batch_size
        self.index = 0
        self._cache = list(queryset)  # Casting queryset to list
    
    def __iter__(self):
        """
        Demonstrates: Iterator protocol - returns self
        """
        self.index = 0
        return self
    
    def __next__(self) -> Movie:
        """
        Demonstrates: __next__ for iterator, if/else, StopIteration
        """
        if self.index >= len(self._cache):
            raise StopIteration
        
        movie = self._cache[self.index]
        self.index += 1
        return movie
    
    def __len__(self) -> int:
        """
        Demonstrates: __len__ dunder method
        """
        return len(self._cache)
    
    def get_by_genre(self, genre: str):
        """
        Filter iterator by genre.
        
        Demonstrates: For loop, if/else, lambda, filter
        """
        # Using filter with lambda
        filtered = filter(
            lambda m: m.has_genre(genre),  # Lambda function
            self._cache
        )
        return list(filtered)


class RatingStatistics:
    """
    Helper class for rating statistics.
    
    Demonstrates: Classes, __init__, methods, collections (dict),
                 for loops, if/else
    """
    
    def __init__(self, ratings_queryset):
        """
        Demonstrates: __init__, self, queryset to list casting
        """
        self.ratings = list(ratings_queryset)
        self._stats_cache = {}  # dict for caching
    
    def get_stats_by_genre(self) -> dict:
        """
        Group ratings by movie genre.
        
        Demonstrates: Collections (dict), for loops, 
                     nested loops, if/else, list append
        """
        genre_ratings = {}  # dict: genre -> list of ratings
        
        # For loop over ratings
        for rating in self.ratings:
            # Get genres for this movie
            genres = rating.movie.get_genres_list()
            
            # Nested loop over genres
            for genre in genres:
                if genre not in genre_ratings:
                    genre_ratings[genre] = []  # Initialize list
                genre_ratings[genre].append(rating.stars)
        
        return genre_ratings
    
    def get_user_genre_preferences(self) -> dict:
        """
        Calculate user preferences by genre.
        
        Demonstrates: Dict comprehension, lambda for calculation
        """
        genre_ratings = self.get_stats_by_genre()
        
        # Dict comprehension with lambda-like calculation
        preferences = {
            genre: sum(ratings) / len(ratings) if ratings else 0
            for genre, ratings in genre_ratings.items()
        }
        
        return preferences
