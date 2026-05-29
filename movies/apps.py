from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class MoviesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'movies'
    verbose_name = 'CineSense Movies'
    
    def ready(self):
        """Auto-seed database after migrations."""
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver
        
        @receiver(post_migrate)
        def seed_database(sender, **kwargs):
            """Seed movies if database is empty."""
            if sender.name == 'movies':
                try:
                    from movies.models import Movie
                    if Movie.objects.count() == 0:
                        from django.core.management import call_command
                        from io import StringIO
                        out = StringIO()
                        call_command('seed_movies', stdout=out)
                        logger.info(f"[CineSense] {out.getvalue().strip()}")
                except Exception as e:
                    logger.warning(f"[CineSense] Post-migrate seed failed (non-fatal): {e}")
