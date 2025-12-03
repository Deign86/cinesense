"""
Management command to fetch movie posters from OMDB API.
Updates existing movies with poster URLs from IMDB.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from movies.models import Movie
from movies.services.external_apis import OMDBApiClient
import time


class Command(BaseCommand):
    help = 'Fetch movie posters from OMDB API for all movies without posters'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Fetch posters for all movies, including those with existing posters',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.5,
            help='Delay between API requests in seconds (default: 0.5)',
        )

    def handle(self, *args, **options):
        client = OMDBApiClient()
        
        if not client.api_key:
            self.stdout.write(self.style.ERROR('OMDB API key not configured. Add OMDB_API_KEY to your .env file.'))
            return
        
        # Get movies to update
        if options['all']:
            movies = Movie.objects.all()
        else:
            movies = Movie.objects.filter(poster_path='') | Movie.objects.filter(poster_path__isnull=True)
        
        total = movies.count()
        updated = 0
        failed = 0
        
        self.stdout.write(f'Fetching posters for {total} movies...\n')
        
        for i, movie in enumerate(movies, 1):
            self.stdout.write(f'[{i}/{total}] Fetching poster for: {movie.title} ({movie.year})... ', ending='')
            
            try:
                # Search OMDB by title and year
                movie_data = client.search_by_title(movie.title, movie.year)
                
                if movie_data and movie_data.poster and movie_data.poster != 'N/A':
                    movie.poster_path = movie_data.poster
                    movie.save(update_fields=['poster_path'])
                    updated += 1
                    self.stdout.write(self.style.SUCCESS('✓'))
                else:
                    # Try without year
                    movie_data = client.search_by_title(movie.title)
                    if movie_data and movie_data.poster and movie_data.poster != 'N/A':
                        movie.poster_path = movie_data.poster
                        movie.save(update_fields=['poster_path'])
                        updated += 1
                        self.stdout.write(self.style.SUCCESS('✓'))
                    else:
                        failed += 1
                        self.stdout.write(self.style.WARNING('not found'))
                        
            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f'error: {e}'))
            
            # Rate limiting
            time.sleep(options['delay'])
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Done! Updated {updated} movies with posters.'))
        if failed:
            self.stdout.write(self.style.WARNING(f'{failed} movies could not be updated.'))
