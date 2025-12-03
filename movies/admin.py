from django.contrib import admin
from .models import Movie, Rating, UserProfile, WatchEvent


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'year', 'genres', 'popularity', 'created_at']
    list_filter = ['year', 'created_at']
    search_fields = ['title', 'genres', 'overview']
    ordering = ['-popularity']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'stars', 'created_at']
    list_filter = ['stars', 'created_at']
    search_fields = ['user__username', 'movie__title']
    raw_id_fields = ['user', 'movie']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'favorite_genres', 'created_at']
    search_fields = ['user__username', 'favorite_genres']


@admin.register(WatchEvent)
class WatchEventAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'watched_at', 'completed']
    list_filter = ['completed', 'watched_at']
    raw_id_fields = ['user', 'movie']
