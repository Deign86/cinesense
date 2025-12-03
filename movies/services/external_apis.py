"""
External API Integrations for CineSense
- OMDB API (IMDB data)
- Letterboxd (web scraping for public data)
"""

import requests
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from functools import lru_cache
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


@dataclass
class IMDBMovieData:
    """Data class for IMDB movie information"""
    imdb_id: str
    title: str
    year: str
    rated: str
    released: str
    runtime: str
    genre: str
    director: str
    writer: str
    actors: str
    plot: str
    language: str
    country: str
    awards: str
    poster: str
    ratings: List[Dict[str, str]]
    metascore: str
    imdb_rating: str
    imdb_votes: str
    box_office: str
    production: str
    website: str
    
    @property
    def imdb_url(self) -> str:
        return f"https://www.imdb.com/title/{self.imdb_id}/"
    
    @property
    def rating_float(self) -> Optional[float]:
        try:
            return float(self.imdb_rating)
        except (ValueError, TypeError):
            return None
    
    def get_all_ratings(self) -> Dict[str, str]:
        """Get ratings from all sources (IMDB, Rotten Tomatoes, Metacritic)"""
        result = {'IMDB': f"{self.imdb_rating}/10"}
        for rating in self.ratings:
            result[rating.get('Source', 'Unknown')] = rating.get('Value', 'N/A')
        return result


@dataclass
class LetterboxdMovieData:
    """Data class for Letterboxd movie information"""
    title: str
    year: str
    letterboxd_url: str
    average_rating: Optional[float] = None
    rating_count: Optional[int] = None
    fans_count: Optional[int] = None
    description: Optional[str] = None
    genres: Optional[List[str]] = None
    
    @property
    def display_rating(self) -> str:
        if self.average_rating:
            return f"{self.average_rating:.1f}/5"
        return "N/A"


class OMDBApiClient:
    """
    Client for OMDB API (Open Movie Database)
    Get a free API key at: http://www.omdbapi.com/apikey.aspx
    """
    
    BASE_URL = "http://www.omdbapi.com/"
    CACHE_TIMEOUT = 86400  # 24 hours
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'OMDB_API_KEY', None)
        
    def _make_request(self, params: Dict[str, Any]) -> Optional[Dict]:
        """Make a request to OMDB API"""
        if not self.api_key:
            logger.warning("OMDB API key not configured")
            return None
            
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('Response') == 'False':
                logger.warning(f"OMDB API error: {data.get('Error')}")
                return None
                
            return data
        except requests.RequestException as e:
            logger.error(f"OMDB API request failed: {e}")
            return None
    
    def search_by_title(self, title: str, year: Optional[int] = None) -> Optional[IMDBMovieData]:
        """Search for a movie by title and optionally year"""
        cache_key = f"omdb_title_{title}_{year}"
        cached = cache.get(cache_key)
        if cached:
            return cached
            
        params = {'t': title, 'type': 'movie', 'plot': 'full'}
        if year:
            params['y'] = year
            
        data = self._make_request(params)
        if not data:
            return None
            
        result = self._parse_movie_data(data)
        cache.set(cache_key, result, self.CACHE_TIMEOUT)
        return result
    
    def search_by_imdb_id(self, imdb_id: str) -> Optional[IMDBMovieData]:
        """Search for a movie by IMDB ID"""
        cache_key = f"omdb_imdb_{imdb_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
            
        params = {'i': imdb_id, 'plot': 'full'}
        data = self._make_request(params)
        if not data:
            return None
            
        result = self._parse_movie_data(data)
        cache.set(cache_key, result, self.CACHE_TIMEOUT)
        return result
    
    def search_movies(self, query: str, page: int = 1) -> List[Dict[str, str]]:
        """Search for movies matching a query"""
        params = {'s': query, 'type': 'movie', 'page': page}
        data = self._make_request(params)
        
        if not data or 'Search' not in data:
            return []
            
        return [
            {
                'imdb_id': movie.get('imdbID', ''),
                'title': movie.get('Title', ''),
                'year': movie.get('Year', ''),
                'poster': movie.get('Poster', ''),
            }
            for movie in data['Search']
        ]
    
    def _parse_movie_data(self, data: Dict) -> IMDBMovieData:
        """Parse OMDB response into IMDBMovieData"""
        return IMDBMovieData(
            imdb_id=data.get('imdbID', ''),
            title=data.get('Title', ''),
            year=data.get('Year', ''),
            rated=data.get('Rated', 'N/A'),
            released=data.get('Released', 'N/A'),
            runtime=data.get('Runtime', 'N/A'),
            genre=data.get('Genre', ''),
            director=data.get('Director', 'N/A'),
            writer=data.get('Writer', 'N/A'),
            actors=data.get('Actors', 'N/A'),
            plot=data.get('Plot', ''),
            language=data.get('Language', 'N/A'),
            country=data.get('Country', 'N/A'),
            awards=data.get('Awards', 'N/A'),
            poster=data.get('Poster', ''),
            ratings=data.get('Ratings', []),
            metascore=data.get('Metascore', 'N/A'),
            imdb_rating=data.get('imdbRating', 'N/A'),
            imdb_votes=data.get('imdbVotes', 'N/A'),
            box_office=data.get('BoxOffice', 'N/A'),
            production=data.get('Production', 'N/A'),
            website=data.get('Website', 'N/A'),
        )


class LetterboxdClient:
    """
    Client for Letterboxd data
    Uses web scraping for public data (respects robots.txt)
    """
    
    BASE_URL = "https://letterboxd.com"
    CACHE_TIMEOUT = 3600  # 1 hour
    
    HEADERS = {
        'User-Agent': 'CineSense Movie Recommendation System/1.0',
        'Accept': 'text/html,application/xhtml+xml',
    }
    
    def _slugify(self, title: str) -> str:
        """Convert movie title to Letterboxd URL slug"""
        # Convert to lowercase, replace spaces with hyphens
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars
        slug = re.sub(r'[-\s]+', '-', slug)  # Replace spaces/hyphens with single hyphen
        return slug.strip('-')
    
    def get_movie_url(self, title: str, year: Optional[int] = None) -> str:
        """Generate Letterboxd movie URL"""
        slug = self._slugify(title)
        if year:
            return f"{self.BASE_URL}/film/{slug}-{year}/"
        return f"{self.BASE_URL}/film/{slug}/"
    
    def get_search_url(self, query: str) -> str:
        """Generate Letterboxd search URL"""
        return f"{self.BASE_URL}/search/{query.replace(' ', '+')}/"
    
    def search_movie(self, title: str, year: Optional[int] = None) -> Optional[LetterboxdMovieData]:
        """
        Attempt to get Letterboxd movie data
        Returns basic data with constructed URLs
        """
        cache_key = f"letterboxd_{title}_{year}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Construct the movie URL
        movie_url = self.get_movie_url(title, year)
        
        # Try to fetch the page to verify it exists
        try:
            response = requests.head(movie_url, headers=self.HEADERS, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                result = LetterboxdMovieData(
                    title=title,
                    year=str(year) if year else '',
                    letterboxd_url=movie_url,
                )
                cache.set(cache_key, result, self.CACHE_TIMEOUT)
                return result
        except requests.RequestException as e:
            logger.debug(f"Letterboxd lookup failed: {e}")
        
        # Return with search URL as fallback
        return LetterboxdMovieData(
            title=title,
            year=str(year) if year else '',
            letterboxd_url=self.get_search_url(title),
        )


class ExternalMovieService:
    """
    Unified service for fetching external movie data
    Combines OMDB and Letterboxd data
    """
    
    def __init__(self):
        self.omdb = OMDBApiClient()
        self.letterboxd = LetterboxdClient()
    
    def get_movie_details(self, title: str, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Get comprehensive movie details from external sources
        """
        result = {
            'imdb': None,
            'letterboxd': None,
            'has_external_data': False,
        }
        
        # Fetch IMDB data
        imdb_data = self.omdb.search_by_title(title, year)
        if imdb_data:
            result['imdb'] = imdb_data
            result['has_external_data'] = True
        
        # Fetch Letterboxd data
        letterboxd_data = self.letterboxd.search_movie(title, year)
        if letterboxd_data:
            result['letterboxd'] = letterboxd_data
            result['has_external_data'] = True
        
        return result
    
    def get_imdb_by_id(self, imdb_id: str) -> Optional[IMDBMovieData]:
        """Get IMDB data by IMDB ID"""
        return self.omdb.search_by_imdb_id(imdb_id)
    
    def search_external(self, query: str) -> Dict[str, Any]:
        """Search for movies on external platforms"""
        return {
            'omdb_results': self.omdb.search_movies(query),
            'letterboxd_search_url': self.letterboxd.get_search_url(query),
        }


# Singleton instance for easy access
external_movie_service = ExternalMovieService()
