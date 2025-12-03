"""
CineSense URL Configuration for Movies App

Demonstrates: Django URL patterns, path converters
"""

from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Movie browsing
    path('movies/', views.MovieListView.as_view(), name='movie_list'),
    path('movies/<int:pk>/', views.MovieDetailView.as_view(), name='movie_detail'),
    path('movies/<int:pk>/rate/', views.rate_movie, name='rate_movie'),
    path('movies/add/', views.add_movie, name='add_movie'),
    
    # Genres
    path('genres/', views.all_genres, name='all_genres'),
    path('genres/<str:genre>/', views.genre_movies, name='genre_movies'),
    
    # User features
    path('my-ratings/', views.user_ratings, name='user_ratings'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('recommendations/', views.RecommendationsView.as_view(), name='recommendations'),
    
    # API
    path('api/search/', views.search_api, name='search_api'),
]
