"""
CineSense Movie Recommender
===========================

Demonstrates:
- NumPy arrays and feature matrices
- Linear regression (scikit-learn)
- Custom iterators for recommendations
- Classes with __init__, __str__, methods
- Collections (list, dict, set)
- For loops and while loops
- If/else conditional logic
- Lambdas for sorting
- SciPy for distance calculations
"""

import numpy as np
from scipy import spatial
from scipy import stats as scipy_stats
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from typing import Dict, List, Tuple, Optional, Iterator, Any
from collections import defaultdict


class MovieRecommender:
    """
    ML-based movie recommendation system using linear regression.
    
    Demonstrates: Classes, __init__, methods, NumPy feature matrices,
                 Linear regression, custom iterators
    """
    
    def __init__(self, alpha: float = 1.0):
        """
        Initialize recommender.
        
        Demonstrates: __init__, self, default parameters
        """
        self.alpha = alpha  # Regularization parameter
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Feature configuration - dict
        self.feature_config = {
            'use_genres': True,
            'use_popularity': True,
            'use_year': True,
            'use_runtime': False,
        }
        
        # Caches - collections
        self._genre_encoder = {}  # dict: genre -> index
        self._all_genres = []  # list of genres
        self._user_profile = {}  # dict for user preferences
        self._movie_features = {}  # dict: movie_id -> feature vector
    
    def __str__(self) -> str:
        """
        String representation.
        
        Demonstrates: __str__, f-strings
        """
        status = "trained" if self.is_trained else "not trained"
        return f"MovieRecommender(status={status}, genres={len(self._all_genres)})"
    
    def _build_genre_encoder(self) -> None:
        """
        Build genre to index mapping.
        
        Demonstrates: For loop, set operations, dict building
        """
        from movies.models import Movie
        
        # Collect all genres using set
        all_genres_set = set()  # set for unique genres
        
        # For loop over movies
        for movie in Movie.objects.all():
            genres = movie.get_genres_set()  # set of genres
            all_genres_set |= genres  # set union
        
        # Sort and create encoder
        self._all_genres = sorted(all_genres_set)  # list
        
        # Dict comprehension for encoder
        self._genre_encoder = {
            genre: idx
            for idx, genre in enumerate(self._all_genres)
        }
    
    def _encode_genres(self, genres: List[str]) -> np.ndarray:
        """
        One-hot encode genres.
        
        Demonstrates: NumPy array creation, for loop
        """
        # Create zero array
        encoding = np.zeros(len(self._all_genres), dtype=np.float64)
        
        # For loop to set genre flags
        for genre in genres:
            genre_normalized = genre.strip().title()
            if genre_normalized in self._genre_encoder:
                idx = self._genre_encoder[genre_normalized]
                encoding[idx] = 1.0
        
        return encoding
    
    def _extract_movie_features(self, movie) -> np.ndarray:
        """
        Extract feature vector for a movie.
        
        Demonstrates: NumPy array operations, if/else, 
                     feature engineering
        """
        features = []  # list to build features
        
        # Genre features (one-hot encoded)
        if self.feature_config['use_genres']:
            genre_encoding = self._encode_genres(movie.get_genres_list())
            features.extend(genre_encoding.tolist())
        
        # Popularity feature (normalized)
        if self.feature_config['use_popularity']:
            popularity = float(movie.popularity) if movie.popularity else 0.0
            features.append(popularity)
        
        # Year feature (normalized)
        if self.feature_config['use_year']:
            year = float(movie.year) if movie.year else 2000.0
            features.append(year)
        
        # Runtime feature
        if self.feature_config['use_runtime']:
            runtime = float(movie.runtime) if movie.runtime else 120.0
            features.append(runtime)
        
        return np.array(features, dtype=np.float64)
    
    def train(self, user=None) -> Dict[str, Any]:
        """
        Train the recommendation model.
        
        Demonstrates: NumPy feature matrix, Linear regression,
                     For loops, if/else, dict return
        """
        from movies.models import Rating, Movie
        
        # Build genre encoder first
        self._build_genre_encoder()
        
        if not self._all_genres:
            return {'success': False, 'error': 'No genres found'}
        
        # Get ratings
        if user:
            ratings = Rating.objects.filter(user=user).select_related('movie')
        else:
            ratings = Rating.objects.all().select_related('movie')
        
        ratings_list = list(ratings)
        
        # If/else: Check minimum ratings
        if len(ratings_list) < 3:
            return {
                'success': False,
                'error': f'Need at least 3 ratings, have {len(ratings_list)}',
            }
        
        # Build feature matrix and target vector
        X_list = []  # list for feature vectors
        y_list = []  # list for ratings
        
        # For loop over ratings
        for rating in ratings_list:
            features = self._extract_movie_features(rating.movie)
            X_list.append(features)
            y_list.append(float(rating.stars))
            
            # Cache movie features
            self._movie_features[rating.movie.pk] = features
        
        # Convert to NumPy arrays
        X = np.array(X_list, dtype=np.float64)  # Feature matrix
        y = np.array(y_list, dtype=np.float64)  # Target vector
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train linear regression model
        self.model = Ridge(alpha=self.alpha)
        self.model.fit(X_scaled, y)
        
        self.is_trained = True
        
        # Build user profile from ratings
        if user:
            self._build_user_profile(ratings_list)
        
        # Calculate training metrics
        y_pred = self.model.predict(X_scaled)
        mse = float(np.mean((y - y_pred) ** 2))
        r2 = float(self.model.score(X_scaled, y))
        
        return {
            'success': True,
            'n_samples': len(ratings_list),
            'n_features': X.shape[1],
            'mse': round(mse, 4),
            'r2_score': round(r2, 4),
        }
    
    def _build_user_profile(self, ratings: List) -> None:
        """
        Build user preference profile.
        
        Demonstrates: Dict aggregation, for loops, calculations
        """
        genre_ratings = defaultdict(list)  # dict: genre -> list of ratings
        
        # For loop to aggregate by genre
        for rating in ratings:
            genres = rating.movie.get_genres_list()
            for genre in genres:
                genre_ratings[genre].append(rating.stars)
        
        # Calculate average per genre
        self._user_profile = {}
        for genre, stars_list in genre_ratings.items():
            # NumPy mean
            avg = float(np.mean(stars_list))
            self._user_profile[genre] = {
                'mean': round(avg, 2),
                'count': len(stars_list),
                'std': round(float(np.std(stars_list)), 2),
            }
    
    def predict(self, movie) -> float:
        """
        Predict rating for a movie.
        
        Demonstrates: NumPy operations, if/else
        """
        if not self.is_trained:
            return 3.0  # Default prediction
        
        # Extract features
        features = self._extract_movie_features(movie)
        
        # Reshape for prediction (1 sample)
        X = features.reshape(1, -1)
        
        # Scale
        X_scaled = self.scaler.transform(X)
        
        # Predict
        prediction = self.model.predict(X_scaled)[0]
        
        # Clip to valid range
        prediction = float(np.clip(prediction, 0.5, 5.0))
        
        return round(prediction, 2)
    
    def get_recommendations(
        self,
        user,
        n_recommendations: int = 10
    ) -> 'RecommendationIterator':
        """
        Get movie recommendations.
        
        Demonstrates: Custom iterator usage, lambda sorting
        """
        from movies.models import Movie, Rating
        
        # Get movies user hasn't rated
        rated_ids = set(
            Rating.objects.filter(user=user).values_list('movie_id', flat=True)
        )
        
        unrated_movies = Movie.objects.exclude(pk__in=rated_ids)
        
        # Score all unrated movies
        scored_movies = []  # list of (movie, score) tuples
        
        for movie in unrated_movies:
            score = self.predict(movie)
            scored_movies.append((movie, score))
        
        # Sort by score using lambda
        scored_movies.sort(key=lambda x: x[1], reverse=True)
        
        # Take top N
        top_recommendations = scored_movies[:n_recommendations]
        
        # Return as iterator
        return RecommendationIterator(top_recommendations)
    
    def get_genre_based_recommendations(
        self,
        user,
        n_per_genre: int = 3
    ) -> Dict[str, List[Tuple[Any, float]]]:
        """
        Get recommendations organized by genre.
        
        Demonstrates: Dict of lists, for loops, lambda
        """
        from movies.models import Movie, Rating
        
        # Get rated movie IDs
        rated_ids = set(
            Rating.objects.filter(user=user).values_list('movie_id', flat=True)
        )
        
        # Get user's top genres
        top_genres = sorted(
            self._user_profile.items(),
            key=lambda x: x[1]['mean'],
            reverse=True
        )[:5]
        
        genre_recommendations = {}  # dict: genre -> list of (movie, score)
        
        # For each top genre
        for genre, _ in top_genres:
            # Get unrated movies in this genre
            movies = Movie.objects.filter(
                genres__icontains=genre
            ).exclude(pk__in=rated_ids)
            
            # Score and sort
            scored = [
                (movie, self.predict(movie))
                for movie in movies
            ]
            scored.sort(key=lambda x: x[1], reverse=True)
            
            genre_recommendations[genre] = scored[:n_per_genre]
        
        return genre_recommendations
    
    def get_similar_movies(
        self,
        movie,
        n: int = 5
    ) -> List[Tuple[Any, float]]:
        """
        Find similar movies using cosine similarity.
        
        Demonstrates: SciPy distance, NumPy arrays, lambda
        """
        from movies.models import Movie
        
        # Get target movie features
        target_features = self._extract_movie_features(movie)
        
        similarities = []  # list of (movie, similarity)
        
        # Compare with all other movies
        for other_movie in Movie.objects.exclude(pk=movie.pk):
            other_features = self._extract_movie_features(other_movie)
            
            # Calculate cosine similarity using SciPy
            # Note: cosine distance = 1 - cosine similarity
            try:
                distance = spatial.distance.cosine(target_features, other_features)
                similarity = 1 - distance
            except:
                similarity = 0.0
            
            similarities.append((other_movie, similarity))
        
        # Sort by similarity using lambda
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:n]


class RecommendationIterator:
    """
    Custom iterator for recommendations.
    
    Demonstrates: Custom iterator with __iter__ and __next__,
                 __len__, classes, tuple unpacking
    """
    
    def __init__(self, recommendations: List[Tuple[Any, float]]):
        """
        Initialize iterator with recommendation tuples.
        
        Demonstrates: __init__, self, type hints
        """
        self.recommendations = recommendations
        self.index = 0
    
    def __iter__(self) -> Iterator:
        """
        Return iterator (self).
        
        Demonstrates: __iter__ for iterator protocol
        """
        self.index = 0
        return self
    
    def __next__(self) -> Tuple[Any, float]:
        """
        Return next recommendation.
        
        Demonstrates: __next__, StopIteration, tuple return
        """
        if self.index >= len(self.recommendations):
            raise StopIteration
        
        rec = self.recommendations[self.index]
        self.index += 1
        return rec  # Returns (movie, score) tuple
    
    def __len__(self) -> int:
        """
        Return number of recommendations.
        
        Demonstrates: __len__ dunder method
        """
        return len(self.recommendations)
    
    def __str__(self) -> str:
        """
        String representation.
        
        Demonstrates: __str__, f-strings, list comprehension
        """
        if not self.recommendations:
            return "RecommendationIterator(empty)"
        
        # Get top 3 for display
        top_titles = [
            f"{movie.title} ({score:.2f})"
            for movie, score in self.recommendations[:3]
        ]
        return f"RecommendationIterator([{', '.join(top_titles)}, ...])"
    
    def to_list(self) -> List[Dict[str, Any]]:
        """
        Convert to list of dicts.
        
        Demonstrates: List comprehension with dict
        """
        return [
            {
                'movie': movie,
                'movie_title': movie.title,
                'predicted_rating': score,
                'genres': movie.get_genres_list(),
            }
            for movie, score in self.recommendations
        ]


class CollaborativeFilter:
    """
    Simple collaborative filtering recommender.
    
    Demonstrates: Alternative ML approach, NumPy matrix operations
    """
    
    def __init__(self, n_neighbors: int = 5):
        """
        Demonstrates: __init__
        """
        self.n_neighbors = n_neighbors
        self._user_matrix = None
        self._movie_ids = []
        self._user_ids = []
    
    def build_matrix(self) -> None:
        """
        Build user-movie rating matrix.
        
        Demonstrates: NumPy matrix, for loops, dict
        """
        from movies.models import Rating, User, Movie
        
        # Get all users and movies
        self._user_ids = list(
            Rating.objects.values_list('user_id', flat=True).distinct()
        )
        self._movie_ids = list(
            Rating.objects.values_list('movie_id', flat=True).distinct()
        )
        
        # Create mapping dicts
        user_idx = {uid: i for i, uid in enumerate(self._user_ids)}
        movie_idx = {mid: i for i, mid in enumerate(self._movie_ids)}
        
        # Initialize matrix with NaN
        n_users = len(self._user_ids)
        n_movies = len(self._movie_ids)
        self._user_matrix = np.full((n_users, n_movies), np.nan)
        
        # Fill matrix with ratings
        for rating in Rating.objects.all():
            u_idx = user_idx.get(rating.user_id)
            m_idx = movie_idx.get(rating.movie_id)
            
            if u_idx is not None and m_idx is not None:
                self._user_matrix[u_idx, m_idx] = rating.stars
    
    def find_similar_users(self, user_id: int) -> List[Tuple[int, float]]:
        """
        Find similar users using cosine similarity.
        
        Demonstrates: NumPy operations, SciPy distance, loops
        """
        if self._user_matrix is None:
            self.build_matrix()
        
        user_idx_map = {uid: i for i, uid in enumerate(self._user_ids)}
        
        if user_id not in user_idx_map:
            return []
        
        target_idx = user_idx_map[user_id]
        target_ratings = self._user_matrix[target_idx]
        
        similarities = []
        
        for other_idx, other_id in enumerate(self._user_ids):
            if other_id == user_id:
                continue
            
            other_ratings = self._user_matrix[other_idx]
            
            # Find common ratings
            mask = ~np.isnan(target_ratings) & ~np.isnan(other_ratings)
            
            if np.sum(mask) < 2:
                continue
            
            # Calculate similarity
            try:
                dist = spatial.distance.cosine(
                    target_ratings[mask],
                    other_ratings[mask]
                )
                sim = 1 - dist
                similarities.append((other_id, sim))
            except:
                continue
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:self.n_neighbors]


# ==============================================================
# Utility Functions
# ==============================================================

def calculate_rmse(actual: List[float], predicted: List[float]) -> float:
    """
    Calculate Root Mean Square Error.
    
    Demonstrates: NumPy operations, casting
    """
    actual_arr = np.array(actual, dtype=np.float64)
    pred_arr = np.array(predicted, dtype=np.float64)
    
    mse = np.mean((actual_arr - pred_arr) ** 2)
    rmse = np.sqrt(mse)
    
    return float(rmse)


def normalize_features(features: np.ndarray) -> np.ndarray:
    """
    Normalize features to [0, 1] range.
    
    Demonstrates: NumPy min/max operations
    """
    min_vals = np.min(features, axis=0)
    max_vals = np.max(features, axis=0)
    
    # Avoid division by zero
    range_vals = max_vals - min_vals
    range_vals[range_vals == 0] = 1
    
    normalized = (features - min_vals) / range_vals
    
    return normalized
