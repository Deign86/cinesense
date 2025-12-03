"""
TMDB Dataset Parser
====================

Memory-efficient streaming parser for TMDB movie datasets.
Supports both JSON (original TMDB) and CSV (Kaggle) formats.

JSON Format (Original TMDB):
    Dataset URL: https://datasets.tmdb.org/p/0.1/movie-list.json.gz
    Format: JSONL (one JSON object per line) or JSON array

CSV Format (Kaggle - Recommended):
    Dataset URL: https://www.kaggle.com/datasets/alanvourch/tmdb-movies-daily-updates
    File: TMDB_all_movies.csv (696MB, 1M+ movies)
    Columns: id, title, vote_average, vote_count, status, release_date, revenue, 
             runtime, budget, imdb_id, original_language, original_title, overview,
             popularity, tagline, genres, production_companies, production_countries,
             spoken_languages, cast, crew, keywords, poster_path, backdrop_path,
             recommendations, imdb_rating, imdb_vote_count

Usage:
    from movies.services.tmdb_parser import TMDBParser, KaggleTMDBParser
    
    # For Kaggle CSV (recommended):
    for movie_data in KaggleTMDBParser('TMDB_all_movies.csv').stream_movies():
        # movie_data is a dict ready for Movie model
        pass
    
    # For original TMDB JSON:
    for movie_data in TMDBParser('movie-list.json').stream_movies():
        pass
"""

import ast
import csv
import gzip
import json
import os
import re
from datetime import datetime
from decimal import Decimal
from typing import Iterator, Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class TMDBParser:
    """
    Memory-efficient streaming parser for TMDB movie datasets.
    
    Supports:
    - Gzipped files (.json.gz)
    - Plain JSON files (.json)
    - Both JSON array format and JSONL format
    - Streaming parsing for 10M+ records
    """
    
    # TMDB genre ID to name mapping
    GENRE_MAP = {
        28: "Action",
        12: "Adventure",
        16: "Animation",
        35: "Comedy",
        80: "Crime",
        99: "Documentary",
        18: "Drama",
        10751: "Family",
        14: "Fantasy",
        36: "History",
        27: "Horror",
        10402: "Music",
        9648: "Mystery",
        10749: "Romance",
        878: "Science Fiction",
        10770: "TV Movie",
        53: "Thriller",
        10752: "War",
        37: "Western",
    }
    
    def __init__(self, file_path: str):
        """
        Initialize parser with file path.
        
        Args:
            file_path: Path to TMDB JSON file (can be .json or .json.gz)
        """
        self.file_path = file_path
        self.is_gzipped = file_path.endswith('.gz')
        
    def _open_file(self):
        """Open file with appropriate handler (gzip or plain)."""
        if self.is_gzipped:
            return gzip.open(self.file_path, 'rt', encoding='utf-8')
        return open(self.file_path, 'r', encoding='utf-8')
    
    def stream_movies(self) -> Iterator[Dict[str, Any]]:
        """
        Stream movies one at a time from the dataset.
        
        Memory efficient - only holds one movie in memory at a time.
        
        Yields:
            Dict containing movie data from TMDB
        """
        try:
            # Try ijson for true streaming (best for large files)
            import ijson
            yield from self._stream_with_ijson()
        except ImportError:
            # Fallback to line-by-line parsing
            logger.warning("ijson not installed, using fallback parser (slower for large files)")
            yield from self._stream_fallback()
    
    def _stream_with_ijson(self) -> Iterator[Dict[str, Any]]:
        """
        Stream using ijson for memory-efficient parsing.
        
        ijson parses JSON incrementally without loading entire file.
        """
        import ijson
        
        with self._open_file() as f:
            # Try parsing as JSON array first
            try:
                # ijson.items returns iterator over array items
                parser = ijson.items(f, 'item')
                for movie in parser:
                    if self._is_valid_movie(movie):
                        yield movie
            except ijson.JSONError:
                # Fallback: might be JSONL format
                f.seek(0)
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            movie = json.loads(line)
                            if self._is_valid_movie(movie):
                                yield movie
                        except json.JSONDecodeError:
                            continue
    
    def _stream_fallback(self) -> Iterator[Dict[str, Any]]:
        """
        Fallback streaming parser without ijson.
        
        Handles both JSONL and JSON array formats.
        Less memory efficient for JSON arrays but works without dependencies.
        """
        with self._open_file() as f:
            # Peek at first character to determine format
            first_char = f.read(1)
            f.seek(0)
            
            if first_char == '[':
                # JSON array format - need to load chunks
                yield from self._parse_json_array(f)
            else:
                # JSONL format - one JSON object per line
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('[') and not line.startswith(']'):
                        # Remove trailing comma if present
                        if line.endswith(','):
                            line = line[:-1]
                        try:
                            movie = json.loads(line)
                            if self._is_valid_movie(movie):
                                yield movie
                        except json.JSONDecodeError:
                            continue
    
    def _parse_json_array(self, f) -> Iterator[Dict[str, Any]]:
        """
        Parse JSON array format incrementally.
        
        This is a simple line-based parser for JSON arrays where
        each object is on its own line.
        """
        for line in f:
            line = line.strip()
            if not line or line in ['[', ']']:
                continue
            
            # Remove trailing comma
            if line.endswith(','):
                line = line[:-1]
            
            try:
                movie = json.loads(line)
                if self._is_valid_movie(movie):
                    yield movie
            except json.JSONDecodeError:
                continue
    
    def _is_valid_movie(self, movie: Dict[str, Any]) -> bool:
        """
        Validate movie has required fields.
        
        Args:
            movie: Dict with movie data
            
        Returns:
            True if movie has minimum required fields
        """
        return (
            isinstance(movie, dict) and
            movie.get('id') is not None and
            movie.get('title') or movie.get('original_title')
        )
    
    @classmethod
    def parse_genres(cls, genre_ids: List[int]) -> str:
        """
        Convert TMDB genre IDs to comma-separated genre names.
        
        Args:
            genre_ids: List of TMDB genre IDs
            
        Returns:
            Comma-separated genre names string
        """
        if not genre_ids:
            return ''
        
        genre_names = []
        for gid in genre_ids:
            if gid in cls.GENRE_MAP:
                genre_names.append(cls.GENRE_MAP[gid])
        
        return ', '.join(genre_names)
    
    @classmethod
    def parse_release_year(cls, release_date: Optional[str]) -> Optional[int]:
        """
        Extract year from TMDB release date.
        
        Args:
            release_date: Date string in format 'YYYY-MM-DD'
            
        Returns:
            Year as integer or None
        """
        if not release_date:
            return None
        
        try:
            if isinstance(release_date, str) and len(release_date) >= 4:
                year = int(release_date[:4])
                if 1888 <= year <= 2100:
                    return year
        except (ValueError, TypeError):
            pass
        
        return None
    
    @classmethod
    def movie_to_django_fields(cls, movie_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert TMDB movie data to Django Movie model fields.
        
        Args:
            movie_data: Raw TMDB movie dict
            
        Returns:
            Dict of fields for Movie model, or None if invalid
        """
        # Get title (prefer original_title for non-English)
        title = movie_data.get('title') or movie_data.get('original_title')
        if not title:
            return None
        
        # Get year
        year = cls.parse_release_year(movie_data.get('release_date'))
        if not year:
            # Skip movies without valid release year
            return None
        
        # Parse genres
        genre_ids = movie_data.get('genre_ids', [])
        genres = cls.parse_genres(genre_ids)
        
        # Get poster path
        poster_path = movie_data.get('poster_path', '') or ''
        if poster_path and not poster_path.startswith('http'):
            # TMDB poster paths need base URL prepended
            poster_path = f"https://image.tmdb.org/t/p/w500{poster_path}"
        
        # Get popularity (TMDB provides this)
        popularity = movie_data.get('popularity', 0.0)
        try:
            popularity = float(popularity)
        except (ValueError, TypeError):
            popularity = 0.0
        
        # Get overview
        overview = movie_data.get('overview', '') or ''
        
        # Get adult flag (for filtering)
        is_adult = movie_data.get('adult', False)
        
        # Get language
        language = movie_data.get('original_language', '') or ''
        
        return {
            'tmdb_id': int(movie_data['id']),
            'title': title[:255],  # Truncate to field max length
            'year': year,
            'genres': genres[:500],  # Truncate to field max length
            'overview': overview,
            'poster_path': poster_path[:500],
            'popularity': popularity,
            'language': language[:200],
            # These fields will be empty - can be enriched later via OMDB API
            'imdb_id': '',
            'imdb_rating': None,
            'imdb_votes': '',
            'metascore': None,
            'rotten_tomatoes': '',
            'director': '',
            'writer': '',
            'actors': '',
            'rated': '',
            'released': movie_data.get('release_date', '') or '',
            'country': '',
            'awards': '',
            'box_office': '',
            'production': '',
            'runtime': None,
        }


class KaggleTMDBParser:
    """
    Parser for Kaggle TMDB CSV dataset.
    
    Dataset: https://www.kaggle.com/datasets/alanvourch/tmdb-movies-daily-updates
    File: TMDB_all_movies.csv (~696MB, 1M+ movies)
    
    This dataset is RECOMMENDED over the original TMDB JSON because:
    - Includes IMDB ratings pre-computed (imdb_rating, imdb_vote_count)
    - Has cast, crew, and production info already
    - Updated daily
    - Easier to filter (has status field)
    """
    
    # CSV column to Movie model field mapping
    COLUMN_MAP = {
        'id': 'tmdb_id',
        'title': 'title',
        'original_title': 'original_title',
        'release_date': 'released',
        'overview': 'overview',
        'runtime': 'runtime',
        'popularity': 'popularity',
        'poster_path': 'poster_path',
        'backdrop_path': 'backdrop_path',
        'imdb_id': 'imdb_id',
        'imdb_rating': 'imdb_rating',
        'imdb_vote_count': 'imdb_votes',
        'vote_average': 'tmdb_rating',
        'vote_count': 'tmdb_votes',
        'genres': 'genres',
        'cast': 'actors',
        'crew': 'crew',  # Will parse for director/writer
        'production_companies': 'production',
        'production_countries': 'country',
        'spoken_languages': 'language',
        'revenue': 'box_office',
        'budget': 'budget',
        'status': 'status',
        'tagline': 'tagline',
        'keywords': 'keywords',
    }
    
    def __init__(self, file_path: str, chunk_size: int = 10000):
        """
        Initialize parser.
        
        Args:
            file_path: Path to TMDB_all_movies.csv
            chunk_size: Number of rows to process at a time (for pandas)
        """
        self.file_path = file_path
        self.chunk_size = chunk_size
        
    def _parse_json_field(self, value: str) -> Any:
        """
        Safely parse JSON-like string fields from CSV.
        
        Many CSV columns contain JSON arrays/objects as strings.
        """
        if not value or value in ('', '[]', '{}', 'nan', 'None'):
            return None
        
        try:
            # Try JSON first
            return json.loads(value.replace("'", '"'))
        except (json.JSONDecodeError, TypeError):
            try:
                # Try ast.literal_eval for Python literal syntax
                return ast.literal_eval(value)
            except (ValueError, SyntaxError):
                return None
    
    def _extract_genres(self, genres_str: str) -> str:
        """Extract genre names from genres JSON string."""
        parsed = self._parse_json_field(genres_str)
        if not parsed:
            return ''
        
        if isinstance(parsed, list):
            genre_names = []
            for item in parsed:
                if isinstance(item, dict) and 'name' in item:
                    genre_names.append(item['name'])
                elif isinstance(item, str):
                    genre_names.append(item)
            return ', '.join(genre_names)
        return ''
    
    def _extract_cast(self, cast_str: str, limit: int = 10) -> str:
        """Extract actor names from cast JSON string."""
        parsed = self._parse_json_field(cast_str)
        if not parsed:
            return ''
        
        if isinstance(parsed, list):
            actors = []
            for item in parsed[:limit]:
                if isinstance(item, dict) and 'name' in item:
                    actors.append(item['name'])
                elif isinstance(item, str):
                    actors.append(item)
            return ', '.join(actors)
        return ''
    
    def _extract_crew(self, crew_str: str) -> Dict[str, str]:
        """Extract director and writer from crew JSON string."""
        parsed = self._parse_json_field(crew_str)
        result = {'director': '', 'writer': ''}
        
        if not parsed or not isinstance(parsed, list):
            return result
        
        directors = []
        writers = []
        
        for item in parsed:
            if not isinstance(item, dict):
                continue
            job = item.get('job', '').lower()
            name = item.get('name', '')
            
            if job == 'director' and name:
                directors.append(name)
            elif job in ('writer', 'screenplay', 'story') and name:
                writers.append(name)
        
        result['director'] = ', '.join(directors[:3])  # Limit to 3
        result['writer'] = ', '.join(writers[:3])
        return result
    
    def _extract_production_companies(self, prod_str: str) -> str:
        """Extract production company names."""
        parsed = self._parse_json_field(prod_str)
        if not parsed:
            return ''
        
        if isinstance(parsed, list):
            companies = []
            for item in parsed[:5]:  # Limit to 5
                if isinstance(item, dict) and 'name' in item:
                    companies.append(item['name'])
                elif isinstance(item, str):
                    companies.append(item)
            return ', '.join(companies)
        return ''
    
    def _extract_countries(self, countries_str: str) -> str:
        """Extract country names."""
        parsed = self._parse_json_field(countries_str)
        if not parsed:
            return ''
        
        if isinstance(parsed, list):
            names = []
            for item in parsed:
                if isinstance(item, dict):
                    name = item.get('name') or item.get('iso_3166_1', '')
                    if name:
                        names.append(name)
                elif isinstance(item, str):
                    names.append(item)
            return ', '.join(names)
        return ''
    
    def _extract_languages(self, lang_str: str) -> str:
        """Extract language names."""
        parsed = self._parse_json_field(lang_str)
        if not parsed:
            return ''
        
        if isinstance(parsed, list):
            names = []
            for item in parsed:
                if isinstance(item, dict):
                    name = item.get('english_name') or item.get('name') or item.get('iso_639_1', '')
                    if name:
                        names.append(name)
                elif isinstance(item, str):
                    names.append(item)
            return ', '.join(names)
        return ''
    
    def _parse_year(self, release_date: str) -> Optional[int]:
        """Extract year from release date."""
        if not release_date or release_date in ('', 'nan', 'None'):
            return None
        
        try:
            if len(str(release_date)) >= 4:
                year = int(str(release_date)[:4])
                if 1888 <= year <= 2100:
                    return year
        except (ValueError, TypeError):
            pass
        return None
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if value is None or value == '' or str(value).lower() in ('nan', 'none', ''):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int."""
        if value is None or value == '' or str(value).lower() in ('nan', 'none', ''):
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def stream_movies(self, only_released: bool = True, min_votes: int = 0) -> Iterator[Dict[str, Any]]:
        """
        Stream movies from CSV file.
        
        Args:
            only_released: If True, only yield movies with status='Released'
            min_votes: Minimum vote count to include (filters obscure movies)
            
        Yields:
            Dict of movie data ready for Movie model
        """
        try:
            import pandas as pd
            yield from self._stream_with_pandas(only_released, min_votes)
        except ImportError:
            logger.warning("pandas not installed, using csv module (slower)")
            yield from self._stream_with_csv(only_released, min_votes)
    
    def _stream_with_pandas(self, only_released: bool, min_votes: int) -> Iterator[Dict[str, Any]]:
        """Stream using pandas for efficient CSV parsing."""
        import pandas as pd
        
        # Read in chunks to handle large files
        for chunk in pd.read_csv(
            self.file_path,
            chunksize=self.chunk_size,
            low_memory=False,
            na_values=['', 'nan', 'None', 'NaN'],
            keep_default_na=True,
            encoding='utf-8',
            on_bad_lines='skip'  # Skip malformed rows
        ):
            for _, row in chunk.iterrows():
                movie = self._row_to_movie(row, only_released, min_votes)
                if movie:
                    yield movie
    
    def _stream_with_csv(self, only_released: bool, min_votes: int) -> Iterator[Dict[str, Any]]:
        """Stream using standard csv module (fallback)."""
        with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                movie = self._row_to_movie(row, only_released, min_votes)
                if movie:
                    yield movie
    
    def _row_to_movie(self, row: Dict[str, Any], only_released: bool, min_votes: int) -> Optional[Dict[str, Any]]:
        """
        Convert a CSV row to Movie model fields.
        
        Args:
            row: CSV row as dict (from pandas or csv.DictReader)
            only_released: Filter for released movies only
            min_votes: Minimum vote threshold
            
        Returns:
            Dict of Movie fields or None if invalid
        """
        # Get basic values with fallbacks
        def get(key, default=''):
            val = row.get(key, default)
            if val is None or (isinstance(val, float) and str(val) == 'nan'):
                return default
            return val
        
        # Filter: only released movies
        status = str(get('status', '')).lower()
        if only_released and status != 'released':
            return None
        
        # Filter: minimum votes
        vote_count = self._safe_int(get('vote_count', 0))
        if min_votes > 0 and (vote_count or 0) < min_votes:
            return None
        
        # Get title (required)
        title = str(get('title', '')) or str(get('original_title', ''))
        if not title:
            return None
        
        # Get year (required for meaningful data)
        year = self._parse_year(get('release_date', ''))
        if not year:
            return None
        
        # Get TMDB ID (required)
        tmdb_id = self._safe_int(get('id'))
        if not tmdb_id:
            return None
        
        # Extract crew info
        crew_info = self._extract_crew(str(get('crew', '[]')))
        
        # Build poster URL
        poster_path = str(get('poster_path', ''))
        if poster_path and not poster_path.startswith('http'):
            poster_path = f"https://image.tmdb.org/t/p/w500{poster_path}"
        
        # Convert revenue to box_office string
        revenue = self._safe_int(get('revenue', 0))
        box_office = f"${revenue:,}" if revenue and revenue > 0 else ''
        
        # Get IMDB rating (pre-computed in Kaggle dataset!)
        imdb_rating = self._safe_float(get('imdb_rating'))
        imdb_votes_raw = self._safe_int(get('imdb_vote_count', 0))
        imdb_votes = f"{imdb_votes_raw:,}" if imdb_votes_raw else ''
        
        return {
            'tmdb_id': tmdb_id,
            'title': title[:255],
            'year': year,
            'genres': self._extract_genres(str(get('genres', '[]')))[:500],
            'overview': str(get('overview', ''))[:5000],
            'poster_path': poster_path[:500],
            'popularity': self._safe_float(get('popularity')) or 0.0,
            'language': self._extract_languages(str(get('spoken_languages', '[]')))[:200],
            'imdb_id': str(get('imdb_id', ''))[:50],
            'imdb_rating': imdb_rating,
            'imdb_votes': imdb_votes[:100],
            'director': crew_info['director'][:500],
            'writer': crew_info['writer'][:500],
            'actors': self._extract_cast(str(get('cast', '[]')))[:1000],
            'released': str(get('release_date', ''))[:100],
            'country': self._extract_countries(str(get('production_countries', '[]')))[:200],
            'production': self._extract_production_companies(str(get('production_companies', '[]')))[:500],
            'runtime': self._safe_int(get('runtime')),
            'box_office': box_office[:100],
            # Fields not in Kaggle dataset - leave empty
            'metascore': None,
            'rotten_tomatoes': '',
            'rated': '',
            'awards': '',
        }
    
    def count_movies(self, only_released: bool = True) -> int:
        """
        Count total movies in file (for progress tracking).
        
        Args:
            only_released: Count only released movies
            
        Returns:
            Approximate movie count
        """
        try:
            import pandas as pd
            # Quick count using pandas
            if only_released:
                count = 0
                for chunk in pd.read_csv(self.file_path, chunksize=50000, usecols=['status']):
                    count += (chunk['status'] == 'Released').sum()
                return count
            else:
                # Just count lines
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return sum(1 for _ in f) - 1  # Minus header
        except Exception as e:
            logger.warning(f"Could not count movies: {e}")
            return 0


def parse_tmdb_file(file_path: str) -> Iterator[Dict[str, Any]]:
    """
    Convenience function to parse TMDB file.
    
    Args:
        file_path: Path to TMDB JSON file
        
    Yields:
        Dicts of Django Movie model fields
    """
    parser = TMDBParser(file_path)
    
    for movie_data in parser.stream_movies():
        fields = TMDBParser.movie_to_django_fields(movie_data)
        if fields:
            yield fields


def parse_kaggle_csv(
    file_path: str,
    only_released: bool = True,
    min_votes: int = 0
) -> Iterator[Dict[str, Any]]:
    """
    Convenience function to parse Kaggle TMDB CSV file.
    
    This is the RECOMMENDED method for bulk import.
    
    Args:
        file_path: Path to TMDB_all_movies.csv
        only_released: Only include released movies
        min_votes: Minimum vote count filter
        
    Yields:
        Dicts of Django Movie model fields (ready for bulk_create)
    """
    parser = KaggleTMDBParser(file_path)
    yield from parser.stream_movies(only_released=only_released, min_votes=min_votes)


def detect_file_format(file_path: str) -> str:
    """
    Detect whether file is CSV or JSON format.
    
    Args:
        file_path: Path to file
        
    Returns:
        'csv' or 'json'
    """
    if file_path.lower().endswith('.csv'):
        return 'csv'
    elif file_path.lower().endswith(('.json', '.json.gz')):
        return 'json'
    
    # Try to detect by content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if ',' in first_line and 'id' in first_line.lower():
                return 'csv'
    except:
        pass
    
    return 'json'


def auto_parse_file(
    file_path: str,
    only_released: bool = True,
    min_votes: int = 0
) -> Iterator[Dict[str, Any]]:
    """
    Automatically detect format and parse TMDB file.
    
    Args:
        file_path: Path to TMDB file (CSV or JSON)
        only_released: For CSV, only released movies
        min_votes: For CSV, minimum votes
        
    Yields:
        Dicts of Django Movie model fields
    """
    format_type = detect_file_format(file_path)
    
    if format_type == 'csv':
        yield from parse_kaggle_csv(file_path, only_released, min_votes)
    else:
        yield from parse_tmdb_file(file_path)


def download_tmdb_dataset(output_path: str = 'movie-list.json.gz') -> str:
    """
    Download the latest TMDB movie dataset (JSON format).
    
    NOTE: For Kaggle CSV dataset (recommended), download manually from:
    https://www.kaggle.com/datasets/alanvourch/tmdb-movies-daily-updates
    
    Args:
        output_path: Where to save the downloaded file
        
    Returns:
        Path to downloaded file
    """
    import requests
    
    url = "https://datasets.tmdb.org/p/0.1/movie-list.json.gz"
    
    print(f"Downloading TMDB dataset from {url}...")
    print("This may take a few minutes (~500MB download)...")
    print("\n💡 TIP: For richer data (IMDB ratings, cast, crew), use Kaggle dataset:")
    print("   https://www.kaggle.com/datasets/alanvourch/tmdb-movies-daily-updates\n")
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    pct = (downloaded / total_size) * 100
                    print(f"\rProgress: {pct:.1f}% ({downloaded / 1024 / 1024:.1f} MB)", end='')
    
    print(f"\n✅ Downloaded to {output_path}")
    return output_path
