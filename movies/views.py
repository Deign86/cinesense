"""
CineSense Views
===============

Demonstrates:
- Django views (function and class-based)
- Collections (list, dict, set) for data processing
- Loops (for, while) for iteration
- If/else conditional logic
- Lambdas for sorting and filtering
- f-strings for dynamic content
- String modification for queries
- Casting between types
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Avg, Count, Q, Value, FloatField
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.conf import settings
from django.urls import reverse_lazy

from .models import Movie, Rating, UserProfile, WatchEvent, MovieIterator
from .forms import RatingForm, MovieSearchForm, MovieForm, QuickRatingForm
from .services.analytics import AnalyticsService
from .services.charts import ChartGenerator
from .services.external_apis import external_movie_service, OMDBApiClient
from .ml.recommender import MovieRecommender

import logging

logger = logging.getLogger(__name__)


def home(request):
    """
    Home page view.
    
    Demonstrates: Collections (list, dict), f-strings, Django ORM
    """
    # Get featured movies (top rated with enough votes)
    featured_movies = Movie.objects.annotate(
        avg_rating=Avg('ratings__stars'),
        num_ratings=Count('ratings')
    ).filter(num_ratings__gte=1).order_by('-avg_rating')[:6]
    
    # Get recent movies - list slicing
    recent_movies = list(Movie.objects.order_by('-created_at')[:6])
    
    # Get popular genres with counts - dict comprehension
    # OPTIMIZATION: Limit to top 5000 popular movies to avoid scanning entire DB
    all_movies = Movie.objects.order_by('-popularity')[:5000]
    genre_counts = {}  # dict: genre -> count
    
    for movie in all_movies:
        # For loop over movies
        genres = movie.get_genres_list()  # list of genres
        for genre in genres:
            # Nested for loop
            if genre in genre_counts:
                genre_counts[genre] += 1
            else:
                genre_counts[genre] = 1
    
    # Sort genres by count using lambda
    popular_genres = sorted(
        genre_counts.items(),
        key=lambda x: x[1],  # Lambda: sort by count (second element)
        reverse=True
    )[:8]  # Top 8 genres
    
    # Build stats dict
    stats = {
        'movie_count': Movie.objects.count(),
        'rating_count': Rating.objects.count(),
        'user_count': UserProfile.objects.count(),
    }
    
    # Context dict for template
    context = {
        'featured_movies': featured_movies,
        'recent_movies': recent_movies,
        'popular_genres': popular_genres,
        'stats': stats,
        'page_title': 'CineSense - Movie Recommendations',  # f-string could be used here
    }
    
    return render(request, 'movies/home.html', context)


def search_suggestions(request):
    """
    API endpoint for search suggestions.
    """
    query = request.GET.get('query', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    movies = Movie.objects.filter(title__icontains=query)[:5]
    results = [{
        'id': m.id, 
        'title': m.title, 
        'year': m.year, 
        'poster_path': m.poster_path
    } for m in movies]
    
    return JsonResponse({'results': results})


class MovieListView(ListView):
    """
    List all movies with search and filtering.
    
    Demonstrates: Class-based views, collections, loops, if/else,
                 string operations, lambdas for sorting
    """
    model = Movie
    template_name = 'movies/movie_list.html'
    context_object_name = 'movies'
    paginate_by = 12
    
    def get_queryset(self):
        """
        Filter and sort movies based on search form.
        
        Demonstrates: If/else branching, string operations,
                     Django ORM filtering, collections (Q objects list)
        """
        queryset = Movie.objects.all()
        
        # Get form data
        form = MovieSearchForm(self.request.GET)
        
        if form.is_valid():
            query = form.cleaned_data.get('query')
            genre = form.cleaned_data.get('genre')
            year_from = form.cleaned_data.get('year_from')
            year_to = form.cleaned_data.get('year_to')
            sort_by = form.cleaned_data.get('sort_by', 'popularity')
            min_rating = form.cleaned_data.get('min_rating')
            
            # Text search with string operations
            if query:
                # String modification: strip and lower
                query = query.strip().lower()
                
                # Build Q objects list for OR filtering
                q_objects = []  # list of Q objects
                
                # Search in title
                q_objects.append(Q(title__icontains=query))
                
                # Search in overview
                q_objects.append(Q(overview__icontains=query))
                
                # Combine Q objects with OR using loop
                combined_q = Q()
                for q in q_objects:
                    combined_q |= q  # OR operation
                
                queryset = queryset.filter(combined_q)
            
            # Genre filter with string matching
            if genre:
                # If/else: different filtering based on genre
                genre_formatted = genre.strip().title()
                queryset = queryset.filter(genres__icontains=genre_formatted)
            
            # Year range filtering
            if year_from:
                queryset = queryset.filter(year__gte=year_from)
            if year_to:
                queryset = queryset.filter(year__lte=year_to)
            
            # Minimum rating filter
            if min_rating:
                min_rating = float(min_rating)  # Casting to float
                queryset = queryset.filter(avg_rating__gte=min_rating)
            
            # Sorting with if/else for different sort options
            if sort_by == 'avg_rating':
                # OPTIMIZATION: Only annotate if specifically sorting by rating
                queryset = queryset.annotate(
                    avg_rating=Coalesce(Avg('ratings__stars'), Value(0.0), output_field=FloatField()),
                    num_ratings=Count('ratings')
                ).order_by('-avg_rating', '-num_ratings')
            elif sort_by:
                # Handle reverse sorting (prefix with -)
                if sort_by.startswith('-'):
                    queryset = queryset.order_by(sort_by)
                else:
                    queryset = queryset.order_by(sort_by)
            else:
                queryset = queryset.order_by('-popularity')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Add search form to context.
        
        Demonstrates: Dict operations, f-strings
        """
        context = super().get_context_data(**kwargs)
        context['search_form'] = MovieSearchForm(self.request.GET)
        
        # Build page title with f-string
        query = self.request.GET.get('query', '')
        if query:
            context['page_title'] = f"Search: {query} - CineSense"
        else:
            context['page_title'] = "Browse Movies - CineSense"
        
        # OPTIMIZATION: Efficiently fetch ratings ONLY for current page
        # This avoids the N+1 problem and expensive full-table annotation
        movies_on_page = context['object_list']
        if movies_on_page:
            movie_ids = [m.pk for m in movies_on_page]
            
            # Fetch annotated movies for this page only
            annotated_movies = Movie.objects.filter(pk__in=movie_ids).annotate(
                avg_rating=Avg('ratings__stars'),
                num_ratings=Count('ratings')
            )
            
            # Create a dict for O(1) lookup: id -> movie
            movie_map = {m.pk: m for m in annotated_movies}
            
            # Replace the movie objects in the context with annotated ones
            # Preserving the original order is crucial
            annotated_list = []
            for original_movie in movies_on_page:
                if original_movie.pk in movie_map:
                    annotated_list.append(movie_map[original_movie.pk])
                else:
                    annotated_list.append(original_movie)
            
            context['movies'] = annotated_list
            context['object_list'] = annotated_list
        
        return context


class MovieDetailView(DetailView):
    """
    Movie detail view with ratings and similar movies.
    
    Demonstrates: DetailView, collections, methods
    """
    model = Movie
    template_name = 'movies/movie_detail.html'
    context_object_name = 'movie'
    
    def get_context_data(self, **kwargs):
        """
        Add ratings and related data to context.
        
        Demonstrates: Collections (list, dict), for loops, if/else
        """
        context = super().get_context_data(**kwargs)
        movie = self.object
        
        # Get ratings list
        ratings = list(movie.ratings.select_related('user').order_by('-created_at')[:10])
        context['ratings'] = ratings
        
        # Calculate rating distribution - dict
        rating_dist = {i: 0 for i in range(1, 6)}  # Dict comprehension
        for rating in movie.ratings.all():
            stars = int(rating.stars)  # Casting to int
            if stars in rating_dist:
                rating_dist[stars] += 1
        context['rating_distribution'] = rating_dist
        
        # Get all unique tags - set
        all_tags = set()  # set for uniqueness
        for rating in movie.ratings.all():
            tags = rating.get_tags_set()  # set of tags
            all_tags |= tags  # set union
        context['all_tags'] = sorted(all_tags)  # convert to sorted list
        
        # Get similar movies using method
        context['similar_movies'] = movie.get_similar_by_genre(limit=4)
        
        # Rating form for logged-in users
        if self.request.user.is_authenticated:
            # Check if user already rated this movie
            existing_rating = Rating.objects.filter(
                user=self.request.user,
                movie=movie
            ).first()
            
            if existing_rating:
                context['user_rating'] = existing_rating
                context['rating_form'] = RatingForm(instance=existing_rating)
            else:
                context['rating_form'] = RatingForm()
        
        # Build title with f-string and format modifier
        avg = movie.average_rating
        context['page_title'] = f"{movie.title} ({movie.year}) - ★{avg:.1f} - CineSense"
        
        # Fetch external data from IMDB and Letterboxd
        external_data = external_movie_service.get_movie_details(movie.title, movie.year)
        context['imdb_data'] = external_data.get('imdb')
        context['letterboxd_data'] = external_data.get('letterboxd')
        context['has_external_data'] = external_data.get('has_external_data', False)
        
        return context


@login_required
def rate_movie(request, pk):
    """
    Handle movie rating submission.
    
    Demonstrates: If/else, form handling, Django ORM, messages
    """
    movie = get_object_or_404(Movie, pk=pk)
    
    # If/else: Check request method
    if request.method == 'POST':
        form = RatingForm(request.POST)
        
        if form.is_valid():
            # Check for existing rating
            existing = Rating.objects.filter(
                user=request.user,
                movie=movie
            ).first()
            
            if existing:
                # Update existing rating
                existing.stars = form.cleaned_data['stars']
                existing.tags = form.cleaned_data['tags']
                existing.review_text = form.cleaned_data['review_text']
                existing.save()
                # f-string message
                messages.success(
                    request,
                    f"Updated your rating for '{movie.title}' to {existing.stars:.1f} stars!"
                )
            else:
                # Create new rating
                rating = form.save(commit=False)
                rating.user = request.user
                rating.movie = movie
                rating.save()
                messages.success(
                    request,
                    f"You rated '{movie.title}' {rating.stars:.1f} stars!"
                )
            
            return redirect('movie_detail', pk=movie.pk)
        else:
            # Form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    return redirect('movie_detail', pk=movie.pk)


class AnalyticsView(View):
    """
    Analytics dashboard view.
    
    Shows personal analytics for logged-in users,
    global analytics for anonymous users.
    
    Demonstrates: Class-based View, analytics service integration,
                 collections for data aggregation
    """
    
    def get(self, request):
        """
        Display analytics dashboard.
        
        Demonstrates: Service integration, dict data, f-strings
        """
        # Check if user is authenticated for personal vs global stats
        is_authenticated = request.user.is_authenticated
        
        # Initialize analytics service (user=None for global stats)
        analytics = AnalyticsService(user=request.user if is_authenticated else None)
        
        # Get various statistics - returns dicts
        genre_stats = analytics.get_genre_statistics()
        rating_stats = analytics.get_rating_statistics()
        watch_patterns = analytics.get_watch_patterns()
        
        # Generate charts
        chart_gen = ChartGenerator(output_dir=settings.MEDIA_ROOT / 'charts')
        
        charts = {}  # dict of chart paths
        
        # Genre distribution chart
        if genre_stats:
            charts['genre_bar'] = chart_gen.create_genre_bar_chart(genre_stats)
            charts['genre_pie'] = chart_gen.create_genre_pie_chart(genre_stats)
        
        # Rating distribution histogram
        if is_authenticated:
            user_ratings = list(
                Rating.objects.filter(user=request.user).values_list('stars', flat=True)
            )
        else:
            user_ratings = list(
                Rating.objects.all().values_list('stars', flat=True)
            )
        
        if user_ratings:
            charts['rating_hist'] = chart_gen.create_rating_histogram(user_ratings)
        
        # Ratings over time line chart
        if rating_stats.get('ratings_over_time'):
            charts['ratings_line'] = chart_gen.create_ratings_timeline(
                rating_stats['ratings_over_time']
            )
        
        if is_authenticated:
            page_title = f"Your Analytics - {request.user.username} - CineSense"
        else:
            page_title = "Global Analytics - CineSense"
        
        context = {
            'genre_stats': genre_stats,
            'rating_stats': rating_stats,
            'watch_patterns': watch_patterns,
            'charts': charts,
            'is_personal': is_authenticated,
            'page_title': page_title,
        }
        
        return render(request, 'movies/analytics.html', context)


class RecommendationsView(LoginRequiredMixin, View):
    """
    ML-powered recommendations view.
    
    Demonstrates: ML integration, custom iterator, collections
    """
    
    def get(self, request):
        """
        Display personalized recommendations.
        
        Demonstrates: ML recommender, iterator pattern, for loops
        """
        # Check if user has enough ratings
        user_rating_count = Rating.objects.filter(user=request.user).count()
        min_ratings = settings.CINESENSE_CONFIG['min_ratings_for_ml']
        
        # If/else: Check for enough data
        if user_rating_count < min_ratings:
            context = {
                'has_recommendations': False,
                'message': f"Please rate at least {min_ratings} movies to get personalized recommendations. You have rated {user_rating_count}.",
                'movies_needed': min_ratings - user_rating_count,
                'page_title': "Get Recommendations - CineSense",
            }
            return render(request, 'movies/recommendations.html', context)
        
        # Initialize recommender
        recommender = MovieRecommender()
        recommender.train(user=request.user)
        
        # Get recommendations using iterator
        rec_iterator = recommender.get_recommendations(
            user=request.user,
            n_recommendations=settings.CINESENSE_CONFIG['max_recommendations']
        )
        
        recommendations = []  # list to store recommendations
        
        # For loop using custom iterator
        for movie, score in rec_iterator:
            recommendations.append({
                'movie': movie,
                'score': score,
                'score_display': f"{score:.2f}",  # f-string format
            })
        
        # Also get genre-based recommendations
        genre_recs = recommender.get_genre_based_recommendations(
            user=request.user,
            n_per_genre=3
        )
        
        context = {
            'has_recommendations': True,
            'recommendations': recommendations,
            'genre_recommendations': genre_recs,
            'page_title': f"Recommendations for {request.user.username} - CineSense",
        }
        
        return render(request, 'movies/recommendations.html', context)


def genre_movies(request, genre):
    """
    List movies by genre.
    
    Demonstrates: String operations, filtering, pagination
    """
    # String modification: normalize genre
    genre_normalized = genre.strip().title()
    
    # Filter movies containing this genre
    movies = Movie.objects.filter(
        genres__icontains=genre_normalized
    ).annotate(
        avg_rating=Avg('ratings__stars')
    ).order_by('-popularity')
    
    # Pagination
    paginator = Paginator(movies, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'genre': genre_normalized,
        'page_obj': page_obj,
        'page_title': f"{genre_normalized} Movies - CineSense",  # f-string
    }
    
    return render(request, 'movies/genre_movies.html', context)


def search_api(request):
    """
    JSON API for movie search (AJAX).
    
    Demonstrates: JSON response, list comprehension, lambdas
    """
    query = request.GET.get('q', '').strip().lower()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search movies
    movies = Movie.objects.filter(
        Q(title__icontains=query) | Q(genres__icontains=query)
    )[:10]
    
    # Build results using list comprehension with dict
    results = [
        {
            'id': movie.pk,
            'title': movie.title,
            'year': movie.year,
            'genres': movie.get_genres_list(),
            'display': f"{movie.title} ({movie.year})",  # f-string
        }
        for movie in movies
    ]
    
    # Sort by relevance using lambda
    results.sort(key=lambda x: (
        0 if query in x['title'].lower() else 1,  # Title match first
        x['title'].lower()  # Then alphabetically
    ))
    
    return JsonResponse({'results': results})


@login_required
def user_ratings(request):
    """
    View user's ratings.
    
    Demonstrates: Collections, loops, grouping
    """
    ratings = Rating.objects.filter(
        user=request.user
    ).select_related('movie').order_by('-created_at')
    
    # Group ratings by star level - dict
    grouped = {}  # dict: stars -> list of ratings
    for rating in ratings:
        stars = int(rating.stars)  # Casting to int
        if stars not in grouped:
            grouped[stars] = []
        grouped[stars].append(rating)
    
    # Calculate statistics
    if ratings:
        stars_list = [r.stars for r in ratings]  # list comprehension
        avg_rating = sum(stars_list) / len(stars_list)
        
        # Count by genre using for loop
        genre_counts = {}
        for rating in ratings:
            for genre in rating.movie.get_genres_list():
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Sort genres using lambda
        top_genres = sorted(
            genre_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
    else:
        avg_rating = 0
        top_genres = []
    
    context = {
        'ratings': ratings,
        'grouped_ratings': grouped,
        'average_rating': avg_rating,
        'top_genres': top_genres,
        'page_title': f"My Ratings - {request.user.username} - CineSense",
    }
    
    return render(request, 'movies/user_ratings.html', context)


def all_genres(request):
    """
    List all genres with movie counts.
    
    Demonstrates: Dict for aggregation, for loop, sorting with lambda
    """
    # Get all movies
    movies = Movie.objects.all()
    
    # Count movies per genre using dict
    genre_data = {}  # dict: genre -> {count, avg_rating, movies}
    
    # For loop over movies
    for movie in movies:
        genres = movie.get_genres_list()  # list
        avg = movie.average_rating
        
        # Nested loop over genres
        for genre in genres:
            if genre not in genre_data:
                genre_data[genre] = {
                    'count': 0,
                    'total_rating': 0,
                    'rated_count': 0,
                }
            
            genre_data[genre]['count'] += 1
            
            if avg > 0:
                genre_data[genre]['total_rating'] += avg
                genre_data[genre]['rated_count'] += 1
    
    # Calculate average ratings and create list
    genre_list = []
    for genre, data in genre_data.items():
        avg = 0
        if data['rated_count'] > 0:
            avg = data['total_rating'] / data['rated_count']
        
        genre_list.append({
            'name': genre,
            'count': data['count'],
            'average_rating': avg,
            'display_rating': f"{avg:.1f}" if avg > 0 else "No ratings",
        })
    
    # Sort by count using lambda
    genre_list.sort(key=lambda x: x['count'], reverse=True)
    
    context = {
        'genres': genre_list,
        'total_genres': len(genre_list),
        'page_title': "All Genres - CineSense",
    }
    
    return render(request, 'movies/all_genres.html', context)


# ==============================================================
# Admin/Staff Views
# ==============================================================

@login_required
def add_movie(request):
    """
    Add a new movie.
    
    Demonstrates: Form handling, if/else, messages
    """
    if not request.user.is_staff:
        messages.error(request, "Only staff can add movies.")
        return redirect('home')
    
    if request.method == 'POST':
        form = MovieForm(request.POST)
        if form.is_valid():
            movie = form.save()
            messages.success(request, f"Added movie: {movie.title}")
            return redirect('movie_detail', pk=movie.pk)
    else:
        form = MovieForm()
    
    context = {
        'form': form,
        'page_title': "Add Movie - CineSense",
    }
    
    return render(request, 'movies/add_movie.html', context)


# ==============================================================
# Authentication Views
# ==============================================================

class CustomLoginView(LoginView):
    """
    Custom login view with styled template.
    """
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Login - CineSense'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().username}!")
        return super().form_valid(form)


class SignupView(CreateView):
    """
    User registration view.
    """
    form_class = UserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Sign Up - CineSense'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Auto-login after signup
        login(self.request, self.object)
        # Create user profile
        from .models import UserProfile
        UserProfile.objects.get_or_create(user=self.object)
        messages.success(self.request, f"Welcome to CineSense, {self.object.username}! Start rating movies to get personalized recommendations.")
        return response
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
