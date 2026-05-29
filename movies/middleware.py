"""
Auto-seed middleware for Vercel deployment.
Runs migrations + seeds the database on cold start.
SQLite DB is not in the Vercel bundle, so tables must be created at runtime.
"""
import threading
import logging

logger = logging.getLogger(__name__)

_initialized = False
_lock = threading.Lock()


class AutoSeedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        global _initialized
        if not _initialized:
            with _lock:
                if not _initialized:
                    try:
                        # Run migrations first — DB doesn't exist in Vercel bundle
                        from django.core.management import call_command
                        call_command('migrate', '--run-syncdb', verbosity=0)

                        # Seed movies if empty
                        from movies.models import Movie
                        if Movie.objects.count() == 0:
                            from io import StringIO
                            out = StringIO()
                            call_command('seed_movies', stdout=out)
                            logger.info(f"[CineSense] {out.getvalue().strip()}")

                        _initialized = True
                    except Exception as e:
                        logger.warning(f"[CineSense] Init failed (will retry): {e}")
                        # Do NOT set _initialized — allow retry on next request
        return self.get_response(request)
