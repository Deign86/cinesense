# 🎬 CineSense - Movie Recommendation System

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2-green.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

> An intelligent movie recommendation system built with Django, featuring machine learning-powered recommendations, external API integrations, and a beautiful dark-themed UI.

---

## 📋 Table of Contents

- [Features](#features)
- [External Integrations](#external-integrations)
- [Python Topics Demonstrated](#python-topics-demonstrated)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [API Configuration](#api-configuration)
- [Usage](#usage)
- [API Overview](#api-overview)
- [Topic Locations Reference](#topic-locations-reference)

## ✨ Features

### Core Functionality
- 🎯 **Smart Movie Recommendations** - ML-powered personalized suggestions using Ridge Regression
- ⭐ **Rating System** - Rate movies and get tailored recommendations
- 🔍 **Advanced Search** - Search by title, genre, director, or year
- 📊 **Analytics Dashboard** - Comprehensive statistics with interactive Matplotlib charts
- 👤 **User Profiles** - Track your movie journey and preferences
- 🖥️ **Desktop GUI** - Tkinter-based desktop client for offline use

### UI/UX Features
- 🌙 **Dark Theme Design** - Sleek dark color palette with amber accents
- ✨ **Smooth Animations** - Page transitions, staggered card loading, hover effects
- 📱 **Responsive Layout** - Works on all devices with Bootstrap 5.3
- 🎨 **Glassmorphism Effects** - Modern backdrop blur styling

---

## 🔗 External Integrations

### 🎬 IMDB Integration (via OMDB API)

The system integrates with the **Open Movie Database (OMDB) API** to fetch rich metadata from IMDB:

| Feature | Description |
|---------|-------------|
| **Movie Posters** | High-quality movie artwork from IMDB |
| **IMDB Ratings** | Official ratings and vote counts |
| **Rotten Tomatoes** | Critical consensus ratings |
| **Metacritic Scores** | Aggregated critic reviews |
| **Cast & Crew** | Director and main cast information |
| **Box Office Data** | Revenue and budget information |
| **Awards** | Oscar nominations and wins |
| **Plot Summaries** | Detailed movie descriptions |

```python
# Example: Fetching IMDB data
from movies.services.external_apis import OMDBClient

client = OMDBClient()
movie_data = client.get_movie_by_title("Inception")
# Returns: poster_url, imdb_rating, rotten_tomatoes, metacritic, director, actors, etc.
```

### 🎞️ Letterboxd Integration

Direct integration with **Letterboxd** - the social network for film lovers:

| Feature | Description |
|---------|-------------|
| **Movie Pages** | Direct links to Letterboxd movie entries |
| **Diary Logging** | Log films to your Letterboxd diary |
| **Watchlist** | Add movies to your Letterboxd watchlist |
| **Social Features** | Access reviews and community ratings |

```python
# Example: Getting Letterboxd URLs
from movies.services.external_apis import LetterboxdClient

client = LetterboxdClient()
urls = client.get_movie_urls("Inception", 2010)
# Returns: film_url, diary_url, watchlist_url
```

### Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CineSense App                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐      ┌─────────────────────────┐  │
│  │   OMDBClient    │      │   LetterboxdClient      │  │
│  │  (external_apis)│      │   (external_apis)       │  │
│  └────────┬────────┘      └───────────┬─────────────┘  │
│           │                           │                 │
│           ▼                           ▼                 │
│  ┌─────────────────┐      ┌─────────────────────────┐  │
│  │   OMDB REST API │      │   Letterboxd URLs       │  │
│  │  (api.omdbapi)  │      │  (letterboxd.com)       │  │
│  └────────┬────────┘      └───────────┬─────────────┘  │
│           │                           │                 │
│           ▼                           ▼                 │
│  ┌─────────────────┐      ┌─────────────────────────┐  │
│  │   IMDB Database │      │   Letterboxd Platform   │  │
│  └─────────────────┘      └─────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 🐍 Python Topics Demonstrated

This project demonstrates ALL of the following Python concepts:

| Topic | Location | Description |
|-------|----------|-------------|
| Casting | `forms.py`, `cli_tools/`, `tkinter_client/` | int(), float(), str() conversions |
| Collections (list) | Throughout | Movie lists, genre lists, rating lists |
| Collections (tuple) | `views.py`, `services/` | Immutable data pairs |
| Collections (set) | `views.py`, `services/analytics.py` | Unique genre extraction |
| Collections (dict) | `settings.py`, `services/`, `views.py` | Configuration, aggregation |
| String Modification | `models.py`, `forms.py`, `views.py` | strip(), lower(), title(), split() |
| User Input (forms) | `forms.py`, Templates | Django forms, HTML forms |
| User Input (CLI) | `cli_tools/` | input() function |
| If/Else | Throughout | Conditional logic everywhere |
| For Loops | Throughout | Iteration over querysets, lists |
| While Loops | `cli_tools/`, `ml/recommender.py` | CLI menus, training loops |
| f-strings | Throughout | String formatting |
| Format Modifiers | Templates, `services/` | `:.2f`, `:.1%`, etc. |
| Lambdas | `views.py`, `services/` | Sorting, filtering |
| Classes/Objects | `models.py`, `services/`, `ml/` | OOP throughout |
| \_\_init\_\_ Method | All classes | Constructor methods |
| \_\_str\_\_ Method | `models.py` | String representation |
| Methods and self | All classes | Instance methods |
| Inheritance | `models.py`, `views.py` | TimestampedModel, CBVs |
| Custom Iterators | `models.py`, `services/charts.py`, `ml/` | MovieIterator, ChartIterator |
| Database (Django ORM) | `models.py`, `views.py` | Full ORM usage |
| NumPy Arrays | `services/analytics.py`, `ml/` | Numerical computations |
| SciPy | `services/analytics.py` | Statistical functions |
| Matplotlib | `services/charts.py` | Chart generation |
| Machine Learning | `ml/recommender.py` | Linear regression |
| Statistics | `services/analytics.py` | mean, median, mode, std |
| Django MVC | Full stack | Models, Views, Templates |
| Tkinter | `tkinter_client/` | Desktop GUI |

## 📁 Project Structure

```
cinesense_project/
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── README.md                    # This file
│
├── cinesense_project/           # Main Django project
│   ├── __init__.py
│   ├── settings.py              # Configuration (dict, CINESENSE_CONFIG)
│   ├── urls.py                  # URL routing
│   ├── wsgi.py                  # WSGI entry point
│   └── asgi.py                  # ASGI entry point
│
├── movies/                      # Main Django app
│   ├── __init__.py
│   ├── models.py                # Database models (Classes, __init__, __str__, Inheritance)
│   ├── views.py                 # View functions/classes (Lambdas, If/Else, Loops)
│   ├── forms.py                 # Form classes (Casting, Validation)
│   ├── urls.py                  # App URL patterns
│   ├── admin.py                 # Admin configuration
│   │
│   ├── services/                # Business logic services
│   │   ├── __init__.py
│   │   ├── analytics.py         # NumPy, SciPy statistics
│   │   └── charts.py            # Matplotlib charts
│   │
│   └── ml/                      # Machine Learning
│       ├── __init__.py
│       └── recommender.py       # Linear Regression, Custom Iterators
│
├── templates/                   # HTML templates
│   └── movies/
│       ├── base.html            # Base template with Bootstrap
│       ├── home.html            # Homepage
│       ├── movie_list.html      # Movie listing
│       ├── movie_detail.html    # Movie details
│       ├── analytics.html       # Analytics dashboard
│       ├── recommendations.html # ML recommendations
│       ├── genre_movies.html    # Genre-specific movies
│       ├── all_genres.html      # All genres
│       ├── user_ratings.html    # User ratings
│       └── add_movie.html       # Add movie form
│
├── static/                      # Static files
│   └── css/
│       └── styles.css           # Custom styles
│
├── cli_tools/                   # Command-line tools
│   ├── __init__.py
│   ├── manual_import.py         # Data import CLI (input(), Casting, Loops)
│   └── rating_session.py        # Interactive rating (input(), If/Else)
│
└── tkinter_client/              # Desktop GUI
    ├── __init__.py
    └── main.py                  # Tkinter application (Classes, Callbacks)
```

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone/Download the project**
   ```bash
   cd "CineSense Movie Recommendation System"
   cd cinesense_project
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser** (optional, for admin access)
   ```bash
   python manage.py createsuperuser
   ```

6. **Configure environment variables**
   Create a `.env` file in the project root:
   ```env
   # OMDB API Key (get free key at https://www.omdbapi.com/apikey.aspx)
   OMDB_API_KEY=your_api_key_here
   
   # Django Settings (optional)
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Web Interface: http://127.0.0.1:8000/
   - Admin Panel: http://127.0.0.1:8000/admin/

---

## 📥 Bulk Movie Import (1M+ Movies)

CineSense supports bulk importing of **1,000,000+ movies** in under 10 minutes.

### 📊 Dataset Options

| Dataset | Format | Size | Features |
|---------|--------|------|----------|
| **Kaggle TMDB** (Recommended) | CSV | 696 MB | IMDB ratings, cast, crew, production companies |
| TMDB Official | JSON.gz | ~500 MB | Basic info only, requires OMDB enrichment |

### Quick Start (Kaggle CSV - Recommended)

```bash
# Install dependencies
pip install pandas tqdm

# 1. Download from Kaggle:
#    https://www.kaggle.com/datasets/alanvourch/tmdb-movies-daily-updates
#    Download: TMDB_all_movies.csv

# 2. Import movies
python manage.py import_movies --bulk --file=TMDB_all_movies.csv --limit=500000
```

### Step-by-Step Instructions

#### Option A: Kaggle CSV Dataset (RECOMMENDED)

This dataset includes **pre-computed IMDB ratings**, cast, crew, and production info!

1. **Download from Kaggle:**
   - Visit: https://www.kaggle.com/datasets/alanvourch/tmdb-movies-daily-updates
   - Download: `TMDB_all_movies.csv` (~696 MB)
   - Save to your project directory

2. **Run the Import:**
```bash
# Import all released movies with IMDB ratings
python manage.py import_movies --bulk --file=TMDB_all_movies.csv

# Import with minimum vote threshold (higher quality)
python manage.py import_movies --bulk --file=TMDB_all_movies.csv --min-votes=100

# Import including unreleased movies
python manage.py import_movies --bulk --file=TMDB_all_movies.csv --include-unreleased
```

#### Option B: TMDB Official JSON Dataset

```bash
# Auto-download and import
python manage.py import_movies --bulk --download --limit=500000

# Or download manually:
# 1. Visit: https://datasets.tmdb.org/p/0.1/movie-list.json.gz
# 2. Run:
python manage.py import_movies --bulk --file=movie-list.json.gz
```

### Import Options

| Option | Default | Description |
|--------|---------|-------------|
| `--bulk` | - | Use TMDB bulk dataset import |
| `--file` | `TMDB_all_movies.csv` | Path to dataset (CSV or JSON) |
| `--limit` | `1,000,000` | Maximum movies to import |
| `--batch-size` | `1000` | Movies per batch (tune for memory) |
| `--min-votes` | `0` | Minimum vote count (CSV only) |
| `--min-popularity` | `0.0` | Minimum TMDB popularity score |
| `--include-adult` | `false` | Include adult movies (JSON only) |
| `--include-unreleased` | `false` | Include unreleased movies (CSV only) |
| `--download` | `false` | Auto-download TMDB JSON dataset |

### Performance

| Movies | Time | Rate |
|--------|------|------|
| 100,000 | ~1 min | ~1,700/sec |
| 500,000 | ~5 min | ~1,700/sec |
| 1,000,000 | ~10 min | ~1,700/sec |

> **Note**: Kaggle CSV import includes IMDB ratings automatically - no need for OMDB enrichment!

### Example Output

```
$ python manage.py import_movies --bulk --file=TMDB_all_movies.csv --limit=500000

📁 Detected format: CSV
   ✨ Using Kaggle CSV parser (includes IMDB ratings!)

Loading existing movie IDs for deduplication...
Found 178 existing movies with TMDB IDs

🎬 Starting bulk import from TMDB_all_movies.csv...
   Limit: 500,000 movies
   Batch size: 1,000
   Only released: True
   Min votes: 0

Importing: 100%|██████████| 500000/500000 [04:52<00:00, 1710.42movies/s]

============================================================
✅ BULK IMPORT COMPLETE!
============================================================
   📥 Imported:        487,234 new movies
   ⏭️  Skipped (exist): 178
   ⚠️  Skipped (invalid):12,588
   ⏱️  Time elapsed:    292.4 seconds
   🚀 Import rate:     1,666 movies/second
============================================================

📊 Total movies in database: 487,412
```

### Verify Import

```bash
# Django shell
python manage.py shell

>>> from movies.models import Movie
>>> Movie.objects.count()
487412

>>> Movie.objects.filter(genres__icontains='Action').count()
68432

>>> Movie.objects.order_by('-popularity')[:5].values_list('title', 'year', 'popularity')
<QuerySet [('Avatar', 2009, 150.437), ('Avengers: Endgame', 2019, 134.23), ...]>
```

### Cleanup Duplicates

```bash
# Dry run (see what would be deleted)
python manage.py cleanup_dups

# Actually delete duplicates
python manage.py cleanup_dups --execute

# Dedupe by title+year instead of tmdb_id
python manage.py cleanup_dups --by-title --execute
```

### Enrich with OMDB Data

After bulk import, you can enrich movies with IMDB ratings, cast, and crew data:

```bash
# Enrich existing movies with OMDB data
python manage.py import_movies --omdb --update-existing
```

---

## 🔑 API Configuration

### OMDB API Setup (Required for IMDB Integration)

1. Visit [OMDB API](https://www.omdbapi.com/apikey.aspx)
2. Request a free API key (1,000 requests/day limit)
3. Add to your `.env` file:
   ```env
   OMDB_API_KEY=your_api_key_here
   ```
4. Restart the Django server

### Using External Integrations

The external API features are available on movie detail pages:

- **"View on IMDB"** - Opens the full IMDB page for the movie
- **"Log on Letterboxd"** - Adds the film to your Letterboxd diary
- **"Add to Watchlist"** - Adds to your Letterboxd watchlist

> **Note**: Letterboxd integration works via URL generation and doesn't require an API key.

---

## 📖 Usage

### Web Interface

Navigate to http://127.0.0.1:8000/ to access:

- **Home**: Dashboard with statistics and recent movies
- **Movies**: Browse and search movies
- **Add Movie**: Add new movies to the database
- **Analytics**: View statistical analysis and charts
- **Recommendations**: Get ML-powered movie recommendations

### CLI Tools

**Import movies manually:**
```bash
python cli_tools/manual_import.py
```

**Interactive rating session:**
```bash
python cli_tools/rating_session.py
```

### Tkinter Desktop Client

```bash
python tkinter_client/main.py
```

## 🔗 API Overview

### Models

- **Movie**: title, year, genres, overview, popularity
- **Rating**: user, movie, stars (0.5-5.0), tags
- **UserProfile**: user, favorite_genres, bio
- **WatchEvent**: user, movie, watched_at, completed

### Views

- `home()` - Dashboard view
- `MovieListView` - List all movies with search/filter
- `MovieDetailView` - Movie details with ratings
- `AnalyticsView` - Statistical dashboard
- `RecommendationsView` - ML recommendations

### Services

- `AnalyticsService` - NumPy/SciPy statistics
- `ChartGenerator` - Matplotlib visualizations
- `MovieRecommender` - ML-based recommendations

## 📚 Topic Locations Reference

### Casting (int, float, str)
- `movies/forms.py`: Lines 45-60 (form validation)
- `cli_tools/manual_import.py`: Lines 80-120 (user input conversion)
- `tkinter_client/main.py`: Lines 340-360 (form handling)

### Collections
- **List**: `movies/models.py` line 95 (`get_genres_list()`)
- **Tuple**: `movies/views.py` line 45 (pagination)
- **Set**: `movies/services/analytics.py` line 85 (unique genres)
- **Dict**: `cinesense_project/settings.py` line 130 (CINESENSE_CONFIG)

### String Modification
- `movies/models.py`: `strip()`, `split()`, `title()` in genre parsing
- `movies/forms.py`: Input sanitization with `strip()`, `lower()`
- `cli_tools/manual_import.py`: String formatting throughout

### User Input
- **Forms**: `movies/forms.py` (Django forms), `templates/movies/add_movie.html`
- **CLI**: `cli_tools/manual_import.py` (input() function)

### Control Flow
- **If/Else**: Every file contains conditional logic
- **For Loops**: `movies/views.py` lines 60-80 (queryset iteration)
- **While Loops**: `cli_tools/manual_import.py` lines 50-150 (menu loop)

### f-strings and Format Modifiers
- `movies/models.py`: `__str__` methods throughout
- `templates/movies/analytics.html`: `{{ value|floatformat:2 }}`
- `movies/services/analytics.py`: `f"{value:.2f}"`

### Lambdas
- `movies/views.py`: Line 95 (`sorted(genres, key=lambda x: x[1])`)
- `movies/services/analytics.py`: Line 120 (filtering)

### Object-Oriented Programming
- **Classes**: Every `.py` file defines classes
- **\_\_init\_\_**: All class constructors
- **\_\_str\_\_**: `movies/models.py` for all models
- **Inheritance**: `TimestampedModel` (abstract base class)
- **Methods/self**: Throughout all classes

### Custom Iterators
- `movies/models.py`: `MovieIterator`, `MovieCollection.__iter__`
- `movies/services/charts.py`: `ChartIterator`
- `movies/ml/recommender.py`: `RecommendationIterator`

### Database (Django ORM)
- `movies/models.py`: Model definitions
- `movies/views.py`: QuerySet operations
- `movies/services/analytics.py`: Aggregations

### Scientific Computing
- **NumPy**: `movies/services/analytics.py`, `movies/ml/recommender.py`
- **SciPy**: `movies/services/analytics.py` (stats module)
- **Matplotlib**: `movies/services/charts.py`

### Machine Learning
- `movies/ml/recommender.py`: Ridge regression, feature engineering

### Statistics
- `movies/services/analytics.py`: mean, median, mode, std calculations

### Django Framework
- Models: `movies/models.py`
- Views: `movies/views.py`
- Templates: `templates/movies/`
- Forms: `movies/forms.py`
- URLs: `movies/urls.py`, `cinesense_project/urls.py`

### Tkinter
- `tkinter_client/main.py`: Full GUI application

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- [OMDB API](https://www.omdbapi.com/) - For providing IMDB data access
- [Letterboxd](https://letterboxd.com/) - For the amazing film social platform
- [Bootstrap](https://getbootstrap.com/) - For the responsive UI framework
- [Bootstrap Icons](https://icons.getbootstrap.com/) - For the beautiful iconography
- [Django](https://www.djangoproject.com/) - For the powerful web framework
- [scikit-learn](https://scikit-learn.org/) - For machine learning capabilities

---

<p align="center">
  Made with ❤️ and 🎬<br>
  <strong>CineSense</strong> - A Python learning project demonstrating comprehensive programming concepts
</p>

---

## 🛰️ Vercel Deployment (Environment Variables)

To fix the "DisallowedHost" error on Vercel, configure `ALLOWED_HOSTS` and `DEBUG` as environment variables. You can either add them in the Vercel Dashboard (recommended) or provide a `vercel.json` in the repository (dashboard is preferred for secrets).

- Recommended Environment Variables (Vercel Dashboard → Project → Settings → Environment Variables):
   - **Key:** `ALLOWED_HOSTS` — **Value:** `cinesense-seven.vercel.app,.vercel.app,localhost,127.0.0.1`
   - **Key:** `DEBUG` — **Value:** `False` (set `True` only for development)
   - **Key:** `OMDB_API_KEY` — **Value:** `your_api_key_here` (keep this secret)

- After adding the environment variables in the Dashboard, redeploy the project; the DisallowedHost error should be resolved.

If you'd like, I can:
- Add a `.env` file for local testing from `.env.example` (I created `.env.example` in the repo).
- Walk you step-by-step through adding variables in the Vercel Dashboard.
