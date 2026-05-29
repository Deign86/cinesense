"""
Django settings for cinesense_project project.

CineSense Movie Recommendation System
=====================================
Demonstrates: f-strings, collections (dict), string modification
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# Demonstrates: f-strings with placeholder
SECRET_KEY = f"django-insecure-cinesense-{''.join(['x' for _ in range(40)])}"

# SECURITY WARNING: don't run with debug turned on in production!
# Read DEBUG from environment so production (Vercel) can disable it.
# Use 'True' or 'False' (strings) in environment variables.
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Configure ALLOWED_HOSTS via environment variable for safety and flexibility.
# Example env value: "cinesense-seven.vercel.app,.vercel.app,localhost,127.0.0.1"
_allowed_hosts_env = os.environ.get('ALLOWED_HOSTS')
if _allowed_hosts_env:
    # Split on commas and strip whitespace; ignore empty parts
    ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_env.split(',') if h.strip()]
else:
    # Sensible defaults for local development and the known Vercel host pattern
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'cinesense-seven.vercel.app', '.vercel.app']

# Application definition - Demonstrates: collections (list)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'movies.apps.MoviesConfig',  # Our main app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'movies.middleware.AutoSeedMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cinesense_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cinesense_project.wsgi.application'

# Database - SQLite default for easy setup
# On Vercel, use /tmp for writable SQLite storage (read-only filesystem elsewhere)
import tempfile
_db_path = BASE_DIR / 'db.sqlite3'
if not os.path.exists(str(_db_path)) or not os.access(str(_db_path), os.W_OK):
    # Vercel or other read-only FS: use /tmp
    _db_path = Path(tempfile.gettempdir()) / 'db.sqlite3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _db_path,
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise - serve static files in production
# Use StaticFilesStorage on Vercel (no collectstatic manifest needed)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Media files (uploaded content, generated charts)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CineSense specific settings - Demonstrates: dict collection
CINESENSE_CONFIG = {
    'max_recommendations': 10,
    'min_ratings_for_ml': 5,
    'default_chart_format': 'png',
    'supported_genres': [
        'Action', 'Comedy', 'Drama', 'Horror', 'Sci-Fi',
        'Romance', 'Thriller', 'Documentary', 'Animation', 'Fantasy'
    ],
    'rating_range': (0.5, 5.0),  # tuple: min, max stars
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            # Demonstrates: format string with placeholders
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Authentication settings
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# External API Configuration
# OMDB API - Get a free API key at: http://www.omdbapi.com/apikey.aspx
OMDB_API_KEY = os.environ.get('OMDB_API_KEY', '')  # Set your API key here or via environment variable
