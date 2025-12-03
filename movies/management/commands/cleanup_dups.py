"""
Management command to cleanup duplicate movies in the database.

Usage:
    python manage.py cleanup_dups              # Dry run (show what would be deleted)
    python manage.py cleanup_dups --execute    # Actually delete duplicates
    python manage.py cleanup_dups --by-title   # Dedupe by title+year instead of tmdb_id
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Min
from movies.models import Movie


class Command(BaseCommand):
    help = 'Find and remove duplicate movies from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Actually delete duplicates (default is dry run)',
        )
        parser.add_argument(
            '--by-title',
            action='store_true',
            help='Deduplicate by title+year instead of tmdb_id',
        )
        parser.add_argument(
            '--keep',
            choices=['first', 'last', 'highest-rated', 'most-popular'],
            default='first',
            help='Which duplicate to keep (default: first)',
        )

    def handle(self, *args, **options):
        execute = options['execute']
        by_title = options['by_title']
        keep_strategy = options['keep']
        
        if by_title:
            self._cleanup_by_title(execute, keep_strategy)
        else:
            self._cleanup_by_tmdb_id(execute, keep_strategy)
    
    def _cleanup_by_tmdb_id(self, execute: bool, keep_strategy: str):
        """Remove duplicates based on tmdb_id."""
        self.stdout.write(self.style.HTTP_INFO("\n🔍 Scanning for duplicate tmdb_id entries...\n"))
        
        # Find tmdb_ids that appear more than once
        duplicates = (
            Movie.objects
            .filter(tmdb_id__isnull=False)
            .values('tmdb_id')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
            .order_by('-count')
        )
        
        total_dups = duplicates.count()
        
        if total_dups == 0:
            self.stdout.write(self.style.SUCCESS("✅ No duplicate tmdb_id entries found!"))
            return
        
        self.stdout.write(f"Found {total_dups} tmdb_ids with duplicates\n")
        
        deleted_count = 0
        
        for dup in duplicates:
            tmdb_id = dup['tmdb_id']
            count = dup['count']
            
            # Get all movies with this tmdb_id
            movies = Movie.objects.filter(tmdb_id=tmdb_id)
            
            # Determine which one to keep based on strategy
            if keep_strategy == 'first':
                keep = movies.order_by('id').first()
            elif keep_strategy == 'last':
                keep = movies.order_by('-id').first()
            elif keep_strategy == 'highest-rated':
                keep = movies.order_by('-imdb_rating', '-id').first()
            elif keep_strategy == 'most-popular':
                keep = movies.order_by('-popularity', '-id').first()
            else:
                keep = movies.first()
            
            to_delete = movies.exclude(id=keep.id)
            
            self.stdout.write(
                f"  tmdb_id {tmdb_id}: {count} copies, "
                f"keeping '{keep.title}' (id={keep.id})"
            )
            
            if execute:
                deleted, _ = to_delete.delete()
                deleted_count += deleted
            else:
                deleted_count += to_delete.count()
        
        self.stdout.write("")
        
        if execute:
            self.stdout.write(self.style.SUCCESS(f"✅ Deleted {deleted_count} duplicate movies"))
        else:
            self.stdout.write(self.style.WARNING(
                f"🔍 DRY RUN: Would delete {deleted_count} duplicate movies\n"
                f"   Run with --execute to actually delete"
            ))
        
        self.stdout.write(f"\nTotal movies in database: {Movie.objects.count()}")
    
    def _cleanup_by_title(self, execute: bool, keep_strategy: str):
        """Remove duplicates based on title+year combination."""
        self.stdout.write(self.style.HTTP_INFO("\n🔍 Scanning for duplicate title+year entries...\n"))
        
        # Find title+year combinations that appear more than once
        duplicates = (
            Movie.objects
            .values('title', 'year')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
            .order_by('-count')
        )
        
        total_dups = duplicates.count()
        
        if total_dups == 0:
            self.stdout.write(self.style.SUCCESS("✅ No duplicate title+year entries found!"))
            return
        
        self.stdout.write(f"Found {total_dups} title+year combinations with duplicates\n")
        
        deleted_count = 0
        
        for dup in duplicates[:50]:  # Show first 50
            title = dup['title']
            year = dup['year']
            count = dup['count']
            
            # Get all movies with this title+year
            movies = Movie.objects.filter(title=title, year=year)
            
            # Determine which one to keep based on strategy
            if keep_strategy == 'first':
                keep = movies.order_by('id').first()
            elif keep_strategy == 'last':
                keep = movies.order_by('-id').first()
            elif keep_strategy == 'highest-rated':
                keep = movies.order_by('-imdb_rating', '-id').first()
            elif keep_strategy == 'most-popular':
                keep = movies.order_by('-popularity', '-id').first()
            else:
                keep = movies.first()
            
            to_delete = movies.exclude(id=keep.id)
            
            self.stdout.write(
                f"  '{title}' ({year}): {count} copies, keeping id={keep.id}"
            )
            
            if execute:
                deleted, _ = to_delete.delete()
                deleted_count += deleted
            else:
                deleted_count += to_delete.count()
        
        if total_dups > 50:
            self.stdout.write(f"  ... and {total_dups - 50} more")
        
        self.stdout.write("")
        
        if execute:
            self.stdout.write(self.style.SUCCESS(f"✅ Deleted {deleted_count} duplicate movies"))
        else:
            self.stdout.write(self.style.WARNING(
                f"🔍 DRY RUN: Would delete {deleted_count} duplicate movies\n"
                f"   Run with --execute to actually delete"
            ))
        
        self.stdout.write(f"\nTotal movies in database: {Movie.objects.count()}")
