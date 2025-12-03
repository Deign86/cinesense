"""
CineSense Analytics Service
===========================

Demonstrates:
- NumPy arrays for numerical data
- SciPy statistics (mean, median, mode, std)
- Collections (dict) for genre aggregation
- For loops and while loops
- If/else conditional logic
- Lambdas for data processing
- Classes with __init__ and methods
"""

import numpy as np
from scipy import stats as scipy_stats
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count


class AnalyticsService:
    """
    Service for computing movie analytics and statistics.
    
    Demonstrates: Classes, __init__, methods, self
    """
    
    def __init__(self, user=None):
        """
        Initialize analytics service.
        
        Demonstrates: __init__ method, self, optional parameters
        """
        self.user = user
        self._cache = {}  # dict for caching results
    
    def get_genre_statistics(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate statistics per genre.
        
        Demonstrates: NumPy arrays, SciPy stats (mean, median, mode, std),
                     Dict aggregation, for loops
        """
        from movies.models import Rating
        
        # Get ratings queryset
        if self.user:
            ratings = Rating.objects.filter(user=self.user).select_related('movie')
        else:
            ratings = Rating.objects.all().select_related('movie')
        
        # Aggregate ratings by genre - dict of lists
        genre_ratings = defaultdict(list)  # dict: genre -> list of ratings
        
        # For loop to aggregate ratings by genre
        for rating in ratings:
            genres = rating.movie.get_genres_list()  # list of genres
            
            # Nested for loop over genres
            for genre in genres:
                genre_ratings[genre].append(rating.stars)
        
        # Calculate statistics per genre
        genre_stats = {}  # dict: genre -> stats dict
        
        for genre, ratings_list in genre_ratings.items():
            if len(ratings_list) > 0:
                # Convert to NumPy array
                ratings_array = np.array(ratings_list, dtype=np.float64)
                
                # Calculate statistics using NumPy and SciPy
                mean_val = float(np.mean(ratings_array))  # NumPy mean
                median_val = float(np.median(ratings_array))  # NumPy median
                std_val = float(np.std(ratings_array))  # NumPy std
                
                # SciPy mode (returns ModeResult with mode and count)
                mode_result = scipy_stats.mode(ratings_array, keepdims=True)
                mode_val = float(mode_result.mode[0]) if len(mode_result.mode) > 0 else mean_val
                
                # Additional statistics
                min_val = float(np.min(ratings_array))
                max_val = float(np.max(ratings_array))
                count = len(ratings_array)
                
                # Store in dict
                genre_stats[genre] = {
                    'mean': round(mean_val, 2),
                    'median': round(median_val, 2),
                    'mode': round(mode_val, 2),
                    'std': round(std_val, 2),
                    'min': min_val,
                    'max': max_val,
                    'count': count,
                }
        
        return genre_stats
    
    def get_rating_statistics(self) -> Dict[str, Any]:
        """
        Calculate overall rating statistics.
        
        Demonstrates: NumPy operations, if/else, dict building
        """
        from movies.models import Rating
        
        if self.user:
            ratings_qs = Rating.objects.filter(user=self.user)
        else:
            ratings_qs = Rating.objects.all()
        
        # Convert to list for NumPy
        ratings_list = list(ratings_qs.values_list('stars', flat=True))
        
        # If/else: Check if we have data
        if not ratings_list:
            return {
                'total_ratings': 0,
                'mean': 0,
                'median': 0,
                'mode': 0,
                'std': 0,
                'message': 'No ratings available',
            }
        
        # NumPy array
        ratings_array = np.array(ratings_list, dtype=np.float64)
        
        # Calculate statistics
        stats = {
            'total_ratings': len(ratings_array),
            'mean': round(float(np.mean(ratings_array)), 2),
            'median': round(float(np.median(ratings_array)), 2),
            'std': round(float(np.std(ratings_array)), 2),
            'min': float(np.min(ratings_array)),
            'max': float(np.max(ratings_array)),
            'variance': round(float(np.var(ratings_array)), 2),
        }
        
        # SciPy mode
        mode_result = scipy_stats.mode(ratings_array, keepdims=True)
        stats['mode'] = float(mode_result.mode[0]) if len(mode_result.mode) > 0 else stats['mean']
        
        # Rating distribution - dict
        distribution = {i: 0 for i in range(1, 6)}  # dict comprehension
        for rating in ratings_list:
            bucket = int(rating)  # Casting to int
            if bucket in distribution:
                distribution[bucket] += 1
        stats['distribution'] = distribution
        
        # Ratings over time (for line chart)
        stats['ratings_over_time'] = self._get_ratings_timeline()
        
        return stats
    
    def _get_ratings_timeline(self) -> List[Dict[str, Any]]:
        """
        Get ratings aggregated by date.
        
        Demonstrates: While loop, date operations, dict aggregation
        """
        from movies.models import Rating
        
        if self.user:
            ratings = Rating.objects.filter(user=self.user)
        else:
            ratings = Rating.objects.all()
        
        # Get date range
        first_rating = ratings.order_by('created_at').first()
        if not first_rating:
            return []
        
        start_date = first_rating.created_at.date()
        end_date = timezone.now().date()
        
        # Aggregate by date using while loop
        date_ratings = {}  # dict: date_str -> {count, total, avg}
        current_date = start_date
        
        # While loop over dates
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            date_ratings[date_str] = {
                'date': date_str,
                'count': 0,
                'total': 0.0,
            }
            current_date += timedelta(days=1)
        
        # Fill in data using for loop
        for rating in ratings:
            date_str = rating.created_at.strftime('%Y-%m-%d')
            if date_str in date_ratings:
                date_ratings[date_str]['count'] += 1
                date_ratings[date_str]['total'] += rating.stars
        
        # Calculate averages and convert to list
        timeline = []
        for date_str, data in sorted(date_ratings.items()):
            if data['count'] > 0:
                avg = data['total'] / data['count']
            else:
                avg = None
            
            timeline.append({
                'date': date_str,
                'count': data['count'],
                'average': round(avg, 2) if avg else None,
            })
        
        return timeline
    
    def get_watch_patterns(self) -> Dict[str, Any]:
        """
        Analyze watch patterns.
        
        Demonstrates: Collections, for loops, aggregation
        """
        from movies.models import WatchEvent
        
        if self.user:
            events = WatchEvent.objects.filter(user=self.user).select_related('movie')
        else:
            events = WatchEvent.objects.all().select_related('movie')
        
        # Day of week distribution
        day_counts = {i: 0 for i in range(7)}  # dict: 0-6 -> count
        hour_counts = {i: 0 for i in range(24)}  # dict: 0-23 -> count
        genre_watch_counts = defaultdict(int)  # dict: genre -> count
        
        # For loop over events
        for event in events:
            # Day of week (0=Monday)
            day = event.watched_at.weekday()
            day_counts[day] += 1
            
            # Hour of day
            hour = event.watched_at.hour
            hour_counts[hour] += 1
            
            # Genre counts
            for genre in event.movie.get_genres_list():
                genre_watch_counts[genre] += 1
        
        # Day names mapping
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                     'Friday', 'Saturday', 'Sunday']
        
        # Convert day counts to named dict
        day_distribution = {
            day_names[i]: count 
            for i, count in day_counts.items()
        }
        
        return {
            'day_distribution': day_distribution,
            'hour_distribution': hour_counts,
            'genre_distribution': dict(genre_watch_counts),
            'total_watches': events.count(),
        }
    
    def get_correlation_analysis(self) -> Dict[str, float]:
        """
        Analyze correlations between variables.
        
        Demonstrates: NumPy arrays, SciPy correlation
        """
        from movies.models import Rating, Movie
        
        # Get movies with ratings
        movies = Movie.objects.annotate(
            num_ratings=Count('ratings')
        ).filter(rating_count__gt=0)
        
        if movies.count() < 3:
            return {'message': 'Not enough data for correlation analysis'}
        
        # Build arrays
        popularity_arr = []
        avg_rating_arr = []
        year_arr = []
        
        for movie in movies:
            popularity_arr.append(movie.popularity)
            avg_rating_arr.append(movie.average_rating)
            year_arr.append(movie.year)
        
        # Convert to NumPy arrays
        popularity = np.array(popularity_arr, dtype=np.float64)
        ratings = np.array(avg_rating_arr, dtype=np.float64)
        years = np.array(year_arr, dtype=np.float64)
        
        # Calculate correlations using SciPy
        results = {}
        
        # Popularity vs Rating correlation
        if len(popularity) > 2:
            corr, p_value = scipy_stats.pearsonr(popularity, ratings)
            results['popularity_rating_corr'] = round(float(corr), 3)
            results['popularity_rating_pvalue'] = round(float(p_value), 4)
        
        # Year vs Rating correlation
        if len(years) > 2:
            corr, p_value = scipy_stats.pearsonr(years, ratings)
            results['year_rating_corr'] = round(float(corr), 3)
            results['year_rating_pvalue'] = round(float(p_value), 4)
        
        return results
    
    def get_percentile_ranks(self, movie_id: int) -> Dict[str, float]:
        """
        Calculate percentile ranks for a movie.
        
        Demonstrates: NumPy percentile, if/else
        """
        from movies.models import Movie
        
        try:
            movie = Movie.objects.get(pk=movie_id)
        except Movie.DoesNotExist:
            return {'error': 'Movie not found'}
        
        # Get all movies with ratings
        all_movies = Movie.objects.all()
        
        # Build arrays
        popularities = []
        ratings = []
        
        for m in all_movies:
            popularities.append(m.popularity)
            if m.average_rating > 0:
                ratings.append(m.average_rating)
        
        # Calculate percentiles
        result = {}
        
        if popularities:
            pop_array = np.array(popularities)
            # Use SciPy percentileofscore
            result['popularity_percentile'] = round(
                scipy_stats.percentileofscore(pop_array, movie.popularity), 1
            )
        
        if movie.average_rating > 0 and ratings:
            rating_array = np.array(ratings)
            result['rating_percentile'] = round(
                scipy_stats.percentileofscore(rating_array, movie.average_rating), 1
            )
        
        return result


class GenreAnalyzer:
    """
    Specialized analyzer for genre statistics.
    
    Demonstrates: Classes, __init__, iterator pattern
    """
    
    def __init__(self, genre: str):
        """
        Demonstrates: __init__ with parameters
        """
        self.genre = genre.strip().title()
        self._movies = None
        self._ratings = None
    
    def _load_data(self):
        """
        Lazy load data.
        
        Demonstrates: If/else, Django ORM
        """
        if self._movies is None:
            from movies.models import Movie, Rating
            
            self._movies = list(
                Movie.objects.filter(genres__icontains=self.genre)
            )
            
            movie_ids = [m.pk for m in self._movies]
            self._ratings = list(
                Rating.objects.filter(movie_id__in=movie_ids)
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get genre summary statistics.
        
        Demonstrates: NumPy statistics, dict building
        """
        self._load_data()
        
        if not self._ratings:
            return {
                'genre': self.genre,
                'movie_count': len(self._movies),
                'rating_count': 0,
                'message': 'No ratings for this genre',
            }
        
        # Build ratings array
        ratings_array = np.array(
            [r.stars for r in self._ratings],
            dtype=np.float64
        )
        
        return {
            'genre': self.genre,
            'movie_count': len(self._movies),
            'rating_count': len(self._ratings),
            'mean': round(float(np.mean(ratings_array)), 2),
            'median': round(float(np.median(ratings_array)), 2),
            'std': round(float(np.std(ratings_array)), 2),
            'min': float(np.min(ratings_array)),
            'max': float(np.max(ratings_array)),
        }
    
    def __iter__(self):
        """
        Iterate over movies in this genre.
        
        Demonstrates: Custom iterator, __iter__
        """
        self._load_data()
        self._index = 0
        return self
    
    def __next__(self):
        """
        Demonstrates: __next__ for iterator protocol
        """
        if self._index >= len(self._movies):
            raise StopIteration
        
        movie = self._movies[self._index]
        self._index += 1
        return movie


# ==============================================================
# Utility Functions
# ==============================================================

def calculate_weighted_rating(
    vote_count: int,
    vote_average: float,
    min_votes: int = 10,
    mean_rating: float = 3.0
) -> float:
    """
    Calculate weighted rating (similar to IMDB formula).
    
    Demonstrates: Lambda-like calculation, NumPy operations
    """
    # IMDB weighted rating formula
    # WR = (v/(v+m)) * R + (m/(v+m)) * C
    # v = vote count, m = minimum votes, R = average rating, C = mean rating
    
    v = float(vote_count)
    m = float(min_votes)
    R = float(vote_average)
    C = float(mean_rating)
    
    if v + m == 0:
        return 0.0
    
    weighted = (v / (v + m)) * R + (m / (v + m)) * C
    return round(weighted, 2)


def get_rating_stats_numpy(ratings_list: List[float]) -> Dict[str, float]:
    """
    Calculate statistics using NumPy.
    
    Demonstrates: NumPy array operations, function with type hints
    """
    if not ratings_list:
        return {
            'mean': 0,
            'median': 0,
            'std': 0,
            'count': 0,
        }
    
    arr = np.array(ratings_list, dtype=np.float64)
    
    return {
        'mean': float(np.mean(arr)),
        'median': float(np.median(arr)),
        'std': float(np.std(arr)),
        'min': float(np.min(arr)),
        'max': float(np.max(arr)),
        'count': len(arr),
        'sum': float(np.sum(arr)),
        'variance': float(np.var(arr)),
    }
