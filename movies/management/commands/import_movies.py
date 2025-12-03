"""
Management command to import movies from TMDB bulk dataset OR OMDB API.

BULK IMPORT (Kaggle CSV - RECOMMENDED):
    python manage.py import_movies --bulk --file=TMDB_all_movies.csv --limit=1000000

BULK IMPORT (TMDB JSON - Legacy):
    python manage.py import_movies --bulk --file=movie-list.json.gz --limit=1000000

SINGLE IMPORT (OMDB API - legacy):
    python manage.py import_movies --omdb --limit=100

Features:
- Bulk import 1M+ movies in minutes using Kaggle TMDB dataset
- Auto-detects CSV vs JSON format
- Kaggle CSV includes IMDB ratings, cast, crew pre-parsed!
- Memory-efficient streaming parser (handles 10M+ records)
- Deduplication via tmdb_id
- Progress bar with live stats
- Resume capability (skips existing movies)

Dataset Download:
    Kaggle (recommended): https://www.kaggle.com/datasets/alanvourch/tmdb-movies-daily-updates
    TMDB (legacy JSON):   https://datasets.tmdb.org/p/0.1/movie-list.json.gz
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction, connection
from movies.models import Movie
import time
import os
import sys


# =============================================================================
# TMDB BULK IMPORT FUNCTIONS
# =============================================================================

def bulk_import_tmdb(
    command,
    file_path: str,
    limit: int = 1_000_000,
    batch_size: int = 1000,
    skip_adult: bool = True,
    min_popularity: float = 0.0,
    min_votes: int = 0,
    only_released: bool = True,
):
    """
    Bulk import movies from TMDB dataset file (CSV or JSON).
    
    Supports both:
    - Kaggle CSV (TMDB_all_movies.csv) - RECOMMENDED, has IMDB ratings & cast
    - TMDB JSON (movie-list.json.gz) - Legacy format
    
    Args:
        command: Django management command instance (for stdout)
        file_path: Path to TMDB file (auto-detects CSV vs JSON)
        limit: Maximum number of movies to import
        batch_size: Number of movies per bulk_create batch
        skip_adult: Skip adult movies (JSON only)
        min_popularity: Minimum popularity threshold
        min_votes: Minimum vote count (CSV only, filters obscure movies)
        only_released: Only import released movies (CSV only)
    
    Returns:
        Tuple of (imported_count, skipped_count, total_processed)
    """
    from movies.services.tmdb_parser import (
        TMDBParser, KaggleTMDBParser, detect_file_format, auto_parse_file
    )
    
    # Check if tqdm is available for progress bar
    try:
        from tqdm import tqdm
        use_tqdm = True
    except ImportError:
        use_tqdm = False
        command.stdout.write(command.style.WARNING(
            "Install tqdm for progress bar: pip install tqdm"
        ))
    
    # Detect file format
    file_format = detect_file_format(file_path)
    is_csv = file_format == 'csv'
    
    command.stdout.write(f"\n📁 Detected format: {file_format.upper()}")
    if is_csv:
        command.stdout.write("   ✨ Using Kaggle CSV parser (includes IMDB ratings!)")
    else:
        command.stdout.write("   📦 Using TMDB JSON parser")
    
    # Get existing TMDB IDs for deduplication
    command.stdout.write("\nLoading existing movie IDs for deduplication...")
    existing_ids = set(
        Movie.objects.filter(tmdb_id__isnull=False)
        .values_list('tmdb_id', flat=True)
    )
    command.stdout.write(f"Found {len(existing_ids):,} existing movies with TMDB IDs")
    
    # Stats tracking
    imported = 0
    skipped_existing = 0
    skipped_invalid = 0
    skipped_adult = 0
    skipped_unpopular = 0
    processed = 0
    batch = []
    
    # Start time for ETA calculation
    start_time = time.time()
    
    # Create parser based on format
    if is_csv:
        parser = KaggleTMDBParser(file_path)
        movie_iter = parser.stream_movies(only_released=only_released, min_votes=min_votes)
    else:
        parser = TMDBParser(file_path)
        movie_iter = parser.stream_movies()
    
    # Wrap with tqdm if available
    if use_tqdm:
        # For gzipped files, we can't know total count easily
        # Use the limit as the expected total
        movie_iter = tqdm(
            movie_iter,
            total=limit,
            desc="Importing",
            unit="movies",
            ncols=100,
        )
    
    command.stdout.write(f"\n🎬 Starting bulk import from {file_path}...")
    command.stdout.write(f"   Limit: {limit:,} movies")
    command.stdout.write(f"   Batch size: {batch_size:,}")
    if is_csv:
        command.stdout.write(f"   Only released: {only_released}")
        command.stdout.write(f"   Min votes: {min_votes}")
    command.stdout.write("")
    
    try:
        for movie_data in movie_iter:
            # Check limit
            if imported >= limit:
                break
            
            processed += 1
            
            # For JSON format, apply additional filters
            if not is_csv:
                # Skip adult movies if requested
                if skip_adult and movie_data.get('adult', False):
                    skipped_adult += 1
                    continue
                
                # Check popularity threshold
                popularity = movie_data.get('popularity', 0.0)
                try:
                    popularity = float(popularity)
                except (ValueError, TypeError):
                    popularity = 0.0
                
                if popularity < min_popularity:
                    skipped_unpopular += 1
                    continue
                
                # Convert to Django fields
                fields = TMDBParser.movie_to_django_fields(movie_data)
            else:
                # CSV already returns Django-ready fields
                fields = movie_data
            
            if not fields:
                skipped_invalid += 1
                continue
            
            # Check for duplicates
            tmdb_id = fields['tmdb_id']
            if tmdb_id in existing_ids:
                skipped_existing += 1
                continue
            
            # Add to existing IDs set to catch duplicates within file
            existing_ids.add(tmdb_id)
            
            # Create Movie instance (don't save yet)
            movie = Movie(**fields)
            batch.append(movie)
            
            # Bulk create when batch is full
            if len(batch) >= batch_size:
                _bulk_create_batch(batch, command)
                imported += len(batch)
                batch = []
                
                # Progress update (if not using tqdm)
                if not use_tqdm:
                    elapsed = time.time() - start_time
                    rate = imported / elapsed if elapsed > 0 else 0
                    eta = (limit - imported) / rate if rate > 0 else 0
                    command.stdout.write(
                        f"\rImported: {imported:,} | "
                        f"Rate: {rate:.0f}/sec | "
                        f"ETA: {eta/60:.1f} min",
                        ending=''
                    )
        
        # Final batch
        if batch:
            _bulk_create_batch(batch, command)
            imported += len(batch)
    
    except KeyboardInterrupt:
        command.stdout.write(command.style.WARNING("\n\n⚠️ Import interrupted by user"))
        # Save any remaining batch
        if batch:
            _bulk_create_batch(batch, command)
            imported += len(batch)
    
    # Calculate final stats
    elapsed = time.time() - start_time
    rate = imported / elapsed if elapsed > 0 else 0
    
    # Print summary
    command.stdout.write("\n")
    command.stdout.write(command.style.SUCCESS("=" * 60))
    command.stdout.write(command.style.SUCCESS("✅ BULK IMPORT COMPLETE!"))
    command.stdout.write(command.style.SUCCESS("=" * 60))
    command.stdout.write(f"   📥 Imported:        {imported:,} new movies")
    command.stdout.write(f"   ⏭️  Skipped (exist): {skipped_existing:,}")
    command.stdout.write(f"   ⚠️  Skipped (invalid):{skipped_invalid:,}")
    if skip_adult:
        command.stdout.write(f"   🔞 Skipped (adult):  {skipped_adult:,}")
    if min_popularity > 0:
        command.stdout.write(f"   📉 Skipped (unpop.): {skipped_unpopular:,}")
    command.stdout.write(f"   ⏱️  Time elapsed:    {elapsed:.1f} seconds")
    command.stdout.write(f"   🚀 Import rate:     {rate:.0f} movies/second")
    command.stdout.write(command.style.SUCCESS("=" * 60))
    
    # Total in database
    total_db = Movie.objects.count()
    command.stdout.write(f"\n📊 Total movies in database: {total_db:,}")
    
    return imported, skipped_existing, processed


def _bulk_create_batch(batch, command):
    """
    Bulk create a batch of movies with conflict handling.
    """
    try:
        Movie.objects.bulk_create(
            batch,
            ignore_conflicts=True,  # Skip duplicates silently
            batch_size=1000,
        )
    except Exception as e:
        command.stdout.write(
            command.style.WARNING(f"\nBatch error (retrying individually): {e}")
        )
        # Fallback: try one by one
        for movie in batch:
            try:
                movie.save()
            except Exception:
                pass  # Skip individual failures


# =============================================================================
# LEGACY OMDB SINGLE IMPORT (preserved for compatibility)
# =============================================================================

# Comprehensive list of popular movies across different genres and eras
MOVIES_TO_IMPORT = [
    # Top Rated Classics
    ("The Shawshank Redemption", 1994),
    ("The Godfather", 1972),
    ("The Godfather Part II", 1974),
    ("The Dark Knight", 2008),
    ("12 Angry Men", 1957),
    ("Schindler's List", 1993),
    ("The Lord of the Rings: The Return of the King", 2003),
    ("Pulp Fiction", 1994),
    ("The Lord of the Rings: The Fellowship of the Ring", 2001),
    ("Forrest Gump", 1994),
    
    # Action & Adventure
    ("Inception", 2010),
    ("The Matrix", 1999),
    ("Gladiator", 2000),
    ("The Dark Knight Rises", 2012),
    ("Django Unchained", 2012),
    ("Mad Max: Fury Road", 2015),
    ("John Wick", 2014),
    ("Kill Bill: Vol. 1", 2003),
    ("Top Gun: Maverick", 2022),
    ("Mission: Impossible - Fallout", 2018),
    
    # Sci-Fi
    ("Interstellar", 2014),
    ("Blade Runner", 1982),
    ("Blade Runner 2049", 2017),
    ("The Terminator", 1984),
    ("Terminator 2: Judgment Day", 1991),
    ("Alien", 1979),
    ("Aliens", 1986),
    ("2001: A Space Odyssey", 1968),
    ("E.T. the Extra-Terrestrial", 1982),
    ("Arrival", 2016),
    ("Dune", 2021),
    ("The Martian", 2015),
    ("Gravity", 2013),
    ("District 9", 2009),
    ("Ex Machina", 2014),
    
    # Drama
    ("Fight Club", 1999),
    ("The Departed", 2006),
    ("Goodfellas", 1990),
    ("Se7en", 1995),
    ("The Silence of the Lambs", 1991),
    ("American History X", 1998),
    ("The Green Mile", 1999),
    ("Saving Private Ryan", 1998),
    ("The Prestige", 2006),
    ("Whiplash", 2014),
    ("The Social Network", 2010),
    ("There Will Be Blood", 2007),
    ("No Country for Old Men", 2007),
    ("Prisoners", 2013),
    ("Gone Girl", 2014),
    
    # Comedy
    ("The Big Lebowski", 1998),
    ("Superbad", 2007),
    ("The Hangover", 2009),
    ("Groundhog Day", 1993),
    ("Ferris Bueller's Day Off", 1986),
    ("Airplane!", 1980),
    ("The Grand Budapest Hotel", 2014),
    ("Knives Out", 2019),
    ("In Bruges", 2008),
    ("Hot Fuzz", 2007),
    ("Shaun of the Dead", 2004),
    
    # Horror
    ("The Shining", 1980),
    ("Psycho", 1960),
    ("Get Out", 2017),
    ("A Quiet Place", 2018),
    ("Hereditary", 2018),
    ("The Exorcist", 1973),
    ("The Conjuring", 2013),
    ("It", 2017),
    ("The Babadook", 2014),
    ("Midsommar", 2019),
    
    # Animation
    ("Spirited Away", 2001),
    ("Toy Story", 1995),
    ("Finding Nemo", 2003),
    ("The Lion King", 1994),
    ("Up", 2009),
    ("WALL-E", 2008),
    ("Coco", 2017),
    ("Inside Out", 2015),
    ("How to Train Your Dragon", 2010),
    ("Spider-Man: Into the Spider-Verse", 2018),
    ("Ratatouille", 2007),
    ("The Incredibles", 2004),
    ("Monsters, Inc.", 2001),
    ("Shrek", 2001),
    ("Frozen", 2013),
    
    # International Cinema
    ("Parasite", 2019),
    ("Oldboy", 2003),
    ("Amélie", 2001),
    ("City of God", 2002),
    ("Pan's Labyrinth", 2006),
    ("Cinema Paradiso", 1988),
    ("The Lives of Others", 2006),
    ("Crouching Tiger, Hidden Dragon", 2000),
    ("Seven Samurai", 1954),
    ("Rashomon", 1950),
    
    # Recent Hits (2020s)
    ("Oppenheimer", 2023),
    ("Barbie", 2023),
    ("Everything Everywhere All at Once", 2022),
    ("The Batman", 2022),
    ("No Time to Die", 2021),
    ("Tenet", 2020),
    ("Soul", 2020),
    ("The Father", 2020),
    ("Nomadland", 2020),
    ("Minari", 2020),
    
    # Thriller & Mystery
    ("Memento", 2000),
    ("Shutter Island", 2010),
    ("The Usual Suspects", 1995),
    ("Zodiac", 2007),
    ("Nightcrawler", 2014),
    ("Gone Baby Gone", 2007),
    ("Mystic River", 2003),
    ("The Girl with the Dragon Tattoo", 2011),
    ("The Town", 2010),
    ("Heat", 1995),
    
    # Romance & Drama
    ("Titanic", 1997),
    ("The Notebook", 2004),
    ("Eternal Sunshine of the Spotless Mind", 2004),
    ("La La Land", 2016),
    ("Before Sunrise", 1995),
    ("Pride and Prejudice", 2005),
    ("500 Days of Summer", 2009),
    ("Her", 2013),
    ("Call Me by Your Name", 2017),
    ("Portrait of a Lady on Fire", 2019),
    
    # War Films
    ("Apocalypse Now", 1979),
    ("Full Metal Jacket", 1987),
    ("Platoon", 1986),
    ("Dunkirk", 2017),
    ("1917", 2019),
    ("Hacksaw Ridge", 2016),
    ("Black Hawk Down", 2001),
    ("The Hurt Locker", 2008),
    ("Letters from Iwo Jima", 2006),
    ("Das Boot", 1981),
    
    # Superhero
    ("The Avengers", 2012),
    ("Avengers: Endgame", 2019),
    ("Avengers: Infinity War", 2018),
    ("Black Panther", 2018),
    ("Iron Man", 2008),
    ("Spider-Man: No Way Home", 2021),
    ("Logan", 2017),
    ("Guardians of the Galaxy", 2014),
    ("Thor: Ragnarok", 2017),
    ("Captain America: The Winter Soldier", 2014),
    ("Joker", 2019),
    ("The Suicide Squad", 2021),
    
    # Crime
    ("The Godfather Part III", 1990),
    ("Scarface", 1983),
    ("Casino", 1995),
    ("L.A. Confidential", 1997),
    ("Chinatown", 1974),
    ("The French Connection", 1971),
    ("Training Day", 2001),
    ("Sicario", 2015),
    ("Hell or High Water", 2016),
    ("Wind River", 2017),
    
    # Fantasy
    ("The Lord of the Rings: The Two Towers", 2002),
    ("Harry Potter and the Sorcerer's Stone", 2001),
    ("Harry Potter and the Prisoner of Azkaban", 2004),
    ("The Princess Bride", 1987),
    ("Edward Scissorhands", 1990),
    ("The Wizard of Oz", 1939),
    ("Big Fish", 2003),
    ("The Shape of Water", 2017),
    ("Stardust", 2007),
    ("Coraline", 2009),
    
    # Biographical
    ("Bohemian Rhapsody", 2018),
    ("The Theory of Everything", 2014),
    ("The Imitation Game", 2014),
    ("A Beautiful Mind", 2001),
    ("Catch Me If You Can", 2002),
    ("The Wolf of Wall Street", 2013),
    ("Rocketman", 2019),
    ("The Aviator", 2004),
    ("Spotlight", 2015),
    ("Vice", 2018),
]


class Command(BaseCommand):
    help = '''Import movies from TMDB bulk dataset (1M+ movies) or OMDB API.
    
    BULK IMPORT (Kaggle CSV - recommended):
        python manage.py import_movies --bulk --file=TMDB_all_movies.csv
        
    BULK IMPORT (TMDB JSON - legacy):
        python manage.py import_movies --bulk --file=movie-list.json.gz
        
    LEGACY IMPORT (OMDB API):
        python manage.py import_movies --omdb
    '''

    def add_arguments(self, parser):
        # Import mode
        parser.add_argument(
            '--bulk',
            action='store_true',
            help='Use TMDB bulk dataset import (1M+ movies, fast)',
        )
        parser.add_argument(
            '--omdb',
            action='store_true',
            help='Use legacy OMDB API import (slower, richer metadata)',
        )
        
        # Bulk import options
        parser.add_argument(
            '--file',
            type=str,
            default='TMDB_all_movies.csv',
            help='Path to TMDB dataset file - CSV or JSON (default: TMDB_all_movies.csv)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for bulk_create (default: 1000)',
        )
        parser.add_argument(
            '--min-popularity',
            type=float,
            default=0.0,
            help='Minimum popularity score to import (default: 0.0)',
        )
        parser.add_argument(
            '--min-votes',
            type=int,
            default=0,
            help='Minimum vote count to import - CSV only (default: 0)',
        )
        parser.add_argument(
            '--include-adult',
            action='store_true',
            help='Include adult movies in import (JSON only)',
        )
        parser.add_argument(
            '--include-unreleased',
            action='store_true',
            help='Include unreleased movies (CSV only, default: released only)',
        )
        parser.add_argument(
            '--download',
            action='store_true',
            help='Download TMDB JSON dataset before importing',
        )
        
        # Common options
        parser.add_argument(
            '--limit',
            type=int,
            default=1_000_000,
            help='Limit number of movies to import (default: 1,000,000)',
        )
        
        # Legacy OMDB options
        parser.add_argument(
            '--delay',
            type=float,
            default=0.3,
            help='Delay between API requests in seconds (default: 0.3)',
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update movies that already exist in the database',
        )

    def handle(self, *args, **options):
        # Determine import mode
        use_bulk = options.get('bulk', False)
        use_omdb = options.get('omdb', False)
        
        # Default to bulk if neither specified
        if not use_bulk and not use_omdb:
            use_bulk = True
        
        if use_bulk:
            self._handle_bulk_import(options)
        else:
            self._handle_omdb_import(options)
    
    def _handle_bulk_import(self, options):
        """Handle TMDB bulk dataset import (CSV or JSON)."""
        file_path = options['file']
        
        # Download if requested (JSON only)
        if options.get('download'):
            self.stdout.write(self.style.HTTP_INFO("📥 Downloading TMDB JSON dataset..."))
            self.stdout.write(self.style.WARNING(
                "\n💡 TIP: For better data, use Kaggle CSV instead:\n"
                "   https://www.kaggle.com/datasets/alanvourch/tmdb-movies-daily-updates\n"
            ))
            from movies.services.tmdb_parser import download_tmdb_dataset
            try:
                file_path = download_tmdb_dataset(file_path)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Download failed: {e}"))
                self.stdout.write("\nManual download instructions:")
                self.stdout.write("1. Visit: https://datasets.tmdb.org/p/0.1/movie-list.json.gz")
                self.stdout.write("2. Save to your project directory")
                self.stdout.write("3. Run: python manage.py import_movies --bulk --file=movie-list.json.gz")
                return
        
        # Check file exists
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            self.stdout.write("")
            self.stdout.write("📥 RECOMMENDED: Download Kaggle CSV dataset:")
            self.stdout.write("   https://www.kaggle.com/datasets/alanvourch/tmdb-movies-daily-updates")
            self.stdout.write("   Download: TMDB_all_movies.csv (~696MB)")
            self.stdout.write("")
            self.stdout.write("Alternative: TMDB JSON dataset:")
            self.stdout.write("  python manage.py import_movies --bulk --download")
            self.stdout.write("")
            self.stdout.write("Or download manually:")
            self.stdout.write("  https://datasets.tmdb.org/p/0.1/movie-list.json.gz")
            return
        
        # Run bulk import
        bulk_import_tmdb(
            command=self,
            file_path=file_path,
            limit=options['limit'],
            batch_size=options['batch_size'],
            skip_adult=not options.get('include_adult', False),
            min_popularity=options['min_popularity'],
            min_votes=options.get('min_votes', 0),
            only_released=not options.get('include_unreleased', False),
        )
    
    def _handle_omdb_import(self, options):
        """Handle legacy OMDB API import."""
        from movies.services.external_apis import OMDBApiClient
        
        client = OMDBApiClient()
        
        if not client.api_key:
            self.stdout.write(self.style.ERROR(
                'OMDB API key not configured!\n'
                'Get a free API key at: https://www.omdbapi.com/apikey.aspx\n'
                'Then add to your .env file: OMDB_API_KEY=your_key_here'
            ))
            return
        
        movies_list = MOVIES_TO_IMPORT
        if options['limit'] and options['limit'] < len(movies_list):
            movies_list = movies_list[:options['limit']]
        
        total = len(movies_list)
        created = 0
        updated = 0
        failed = 0
        skipped = 0
        
        self.stdout.write(self.style.HTTP_INFO(f'\n🎬 Importing {total} movies from IMDB via OMDB API...\n'))
        
        for i, (title, year) in enumerate(movies_list, 1):
            # Check if movie exists
            existing = Movie.objects.filter(title__iexact=title, year=year).first()
            
            if existing and not options['update_existing']:
                skipped += 1
                self.stdout.write(f'[{i}/{total}] {title} ({year}) - skipped (exists)')
                continue
            
            self.stdout.write(f'[{i}/{total}] Fetching: {title} ({year})... ', ending='')
            
            try:
                # Fetch from OMDB
                movie_data = client.search_by_title(title, year)
                
                if not movie_data:
                    # Try without year
                    movie_data = client.search_by_title(title)
                
                if not movie_data:
                    failed += 1
                    self.stdout.write(self.style.WARNING('not found'))
                    continue
                
                # Parse runtime (e.g., "142 min" -> 142)
                runtime = None
                if movie_data.runtime and movie_data.runtime != 'N/A':
                    try:
                        runtime = int(movie_data.runtime.replace(' min', '').strip())
                    except ValueError:
                        pass
                
                # Parse IMDB rating
                imdb_rating = None
                if movie_data.imdb_rating and movie_data.imdb_rating != 'N/A':
                    try:
                        imdb_rating = float(movie_data.imdb_rating)
                    except ValueError:
                        pass
                
                # Parse Metascore
                metascore = None
                if movie_data.metascore and movie_data.metascore != 'N/A':
                    try:
                        metascore = int(movie_data.metascore)
                    except ValueError:
                        pass
                
                # Get Rotten Tomatoes from ratings list
                rotten_tomatoes = ''
                for rating in movie_data.ratings:
                    if rating.get('Source') == 'Rotten Tomatoes':
                        rotten_tomatoes = rating.get('Value', '')
                        break
                
                # Calculate popularity score based on IMDB data
                popularity = 0.0
                if imdb_rating:
                    popularity = imdb_rating * 10
                
                # Prepare movie data
                movie_fields = {
                    'genres': movie_data.genre,
                    'overview': movie_data.plot if movie_data.plot != 'N/A' else '',
                    'poster_path': movie_data.poster if movie_data.poster != 'N/A' else '',
                    'runtime': runtime,
                    'imdb_id': movie_data.imdb_id,
                    'imdb_rating': imdb_rating,
                    'imdb_votes': movie_data.imdb_votes if movie_data.imdb_votes != 'N/A' else '',
                    'metascore': metascore,
                    'rotten_tomatoes': rotten_tomatoes,
                    'director': movie_data.director if movie_data.director != 'N/A' else '',
                    'writer': movie_data.writer if movie_data.writer != 'N/A' else '',
                    'actors': movie_data.actors if movie_data.actors != 'N/A' else '',
                    'rated': movie_data.rated if movie_data.rated != 'N/A' else '',
                    'released': movie_data.released if movie_data.released != 'N/A' else '',
                    'language': movie_data.language if movie_data.language != 'N/A' else '',
                    'country': movie_data.country if movie_data.country != 'N/A' else '',
                    'awards': movie_data.awards if movie_data.awards != 'N/A' else '',
                    'box_office': movie_data.box_office if movie_data.box_office != 'N/A' else '',
                    'production': movie_data.production if movie_data.production != 'N/A' else '',
                    'popularity': popularity,
                }
                
                if existing:
                    # Update existing movie
                    for field, value in movie_fields.items():
                        setattr(existing, field, value)
                    existing.save()
                    updated += 1
                    self.stdout.write(self.style.WARNING('updated'))
                else:
                    # Create new movie
                    Movie.objects.create(
                        title=movie_data.title,
                        year=int(movie_data.year) if movie_data.year.isdigit() else year,
                        **movie_fields
                    )
                    created += 1
                    self.stdout.write(self.style.SUCCESS('✓ imported'))
                
            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f'error: {e}'))
            
            # Rate limiting
            time.sleep(options['delay'])
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(f'✅ Import complete!'))
        self.stdout.write(f'   Created: {created} new movies')
        self.stdout.write(f'   Updated: {updated} existing movies')
        self.stdout.write(f'   Skipped: {skipped} (already exist)')
        if failed:
            self.stdout.write(self.style.WARNING(f'   Failed:  {failed} movies'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write('')
        self.stdout.write(f'Total movies in database: {Movie.objects.count()}')

