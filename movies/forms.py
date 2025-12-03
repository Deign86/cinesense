"""
CineSense Forms
===============

Demonstrates:
- Django forms with user input handling
- Form validation and cleaning
- String modification in form processing
- Casting input data
- If/else for validation logic
- Collections (list) for choices
"""

from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Rating, Movie, UserProfile
from typing import List


class RatingForm(forms.ModelForm):
    """
    Form for submitting movie ratings.
    
    Demonstrates: Django ModelForm, form fields, widgets,
                 validation, clean methods
    """
    
    # Custom field with choices
    STAR_CHOICES = [
        (0.5, '½ Star'),
        (1.0, '1 Star'),
        (1.5, '1½ Stars'),
        (2.0, '2 Stars'),
        (2.5, '2½ Stars'),
        (3.0, '3 Stars'),
        (3.5, '3½ Stars'),
        (4.0, '4 Stars'),
        (4.5, '4½ Stars'),
        (5.0, '5 Stars'),
    ]
    
    stars = forms.ChoiceField(
        choices=STAR_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'star-rating'}),
        label='Your Rating'
    )
    
    tags = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tags (comma-separated): fun, exciting, classic'
        }),
        help_text='Add comma-separated tags like: fun, exciting, must-watch'
    )
    
    review_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Write your review here (optional)...'
        }),
        label='Review'
    )
    
    class Meta:
        model = Rating
        fields = ['stars', 'tags', 'review_text']
    
    def clean_stars(self):
        """
        Clean and validate stars field.
        
        Demonstrates: Casting (string to float), if/else validation
        """
        stars = self.cleaned_data.get('stars')
        
        # Casting: form input is string, convert to float
        stars = float(stars)
        
        # If/else validation
        if stars < 0.5:
            raise forms.ValidationError("Rating must be at least 0.5 stars")
        elif stars > 5.0:
            raise forms.ValidationError("Rating cannot exceed 5 stars")
        
        return stars
    
    def clean_tags(self):
        """
        Clean and normalize tags.
        
        Demonstrates: String modification (split, strip, lower),
                     list comprehension, filtering
        """
        tags = self.cleaned_data.get('tags', '')
        
        if not tags:
            return ''
        
        # String operations: split by comma
        tag_list = tags.split(',')
        
        # List comprehension with string methods
        # Strip whitespace, convert to lowercase, filter empty
        cleaned_tags = [
            tag.strip().lower()
            for tag in tag_list
            if tag.strip()  # Filter out empty tags
        ]
        
        # Remove duplicates while preserving order (using dict trick)
        seen = {}
        unique_tags = []
        for tag in cleaned_tags:
            if tag not in seen:
                seen[tag] = True
                unique_tags.append(tag)
        
        # Join back to comma-separated string
        return ', '.join(unique_tags)
    
    def clean_review_text(self):
        """
        Clean review text.
        
        Demonstrates: String modification (strip), if/else
        """
        text = self.cleaned_data.get('review_text', '')
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # If/else: Check for minimum length if provided
        if text and len(text) < 10:
            raise forms.ValidationError(
                "If you write a review, please make it at least 10 characters."
            )
        
        return text


class MovieSearchForm(forms.Form):
    """
    Form for searching movies.
    
    Demonstrates: Non-model form, multiple field types,
                 clean methods, collections (list of choices)
    """
    
    # Genre choices as a list of tuples
    GENRE_CHOICES = [
        ('', 'All Genres'),
        ('action', 'Action'),
        ('comedy', 'Comedy'),
        ('drama', 'Drama'),
        ('horror', 'Horror'),
        ('sci-fi', 'Sci-Fi'),
        ('romance', 'Romance'),
        ('thriller', 'Thriller'),
        ('documentary', 'Documentary'),
        ('animation', 'Animation'),
        ('fantasy', 'Fantasy'),
    ]
    
    SORT_CHOICES = [
        ('popularity', 'Most Popular'),
        ('-popularity', 'Least Popular'),
        ('title', 'Title A-Z'),
        ('-title', 'Title Z-A'),
        ('year', 'Oldest First'),
        ('-year', 'Newest First'),
        ('avg_rating', 'Highest Rated'),
    ]
    
    YEAR_CHOICES = [(None, 'Any Year')] + [
        (year, str(year))
        for year in range(2025, 1899, -1)  # Range: 2025 down to 1900
    ]
    
    query = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search movies...'
        })
    )
    
    genre = forms.ChoiceField(
        required=False,
        choices=GENRE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    year_from = forms.IntegerField(
        required=False,
        min_value=1888,
        max_value=2100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'From year'
        })
    )
    
    year_to = forms.IntegerField(
        required=False,
        min_value=1888,
        max_value=2100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'To year'
        })
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        choices=SORT_CHOICES,
        initial='popularity',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    min_rating = forms.FloatField(
        required=False,
        min_value=0,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min rating',
            'step': '0.5'
        })
    )
    
    def clean(self):
        """
        Cross-field validation.
        
        Demonstrates: If/else, form-level validation
        """
        cleaned_data = super().clean()
        year_from = cleaned_data.get('year_from')
        year_to = cleaned_data.get('year_to')
        
        # Cross-field validation with if/else
        if year_from and year_to:
            if year_from > year_to:
                raise forms.ValidationError(
                    "From year cannot be greater than To year"
                )
        
        return cleaned_data
    
    def clean_query(self):
        """
        Clean search query.
        
        Demonstrates: String modification
        """
        query = self.cleaned_data.get('query', '')
        # Strip and normalize whitespace
        return ' '.join(query.split())


class MovieForm(forms.ModelForm):
    """
    Form for adding/editing movies.
    
    Demonstrates: ModelForm, custom cleaning, genre handling
    """
    
    genres_input = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Genres (comma-separated): Action, Sci-Fi, Drama'
        }),
        help_text='Enter genres separated by commas'
    )
    
    class Meta:
        model = Movie
        fields = ['title', 'year', 'overview', 'runtime', 'popularity']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'overview': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'runtime': forms.NumberInput(attrs={'class': 'form-control'}),
            'popularity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        """
        Demonstrates: __init__ override, parent call with super()
        """
        super().__init__(*args, **kwargs)
        
        # Pre-populate genres_input if editing
        if self.instance and self.instance.pk:
            self.fields['genres_input'].initial = self.instance.genres
    
    def clean_genres_input(self):
        """
        Parse and validate genres.
        
        Demonstrates: String modification, list operations, 
                     for loop, if/else
        """
        genres = self.cleaned_data.get('genres_input', '')
        
        if not genres:
            return ''
        
        # Split and clean genres
        genre_list = []
        for genre in genres.split(','):
            cleaned = genre.strip().title()  # String methods
            if cleaned and len(cleaned) <= 50:  # Validate length
                genre_list.append(cleaned)
        
        # Remove duplicates using set, then sort
        unique_genres = sorted(set(genre_list))
        
        return ', '.join(unique_genres)
    
    def save(self, commit=True):
        """
        Save with genre handling.
        
        Demonstrates: Method override, super() call
        """
        instance = super().save(commit=False)
        
        # Set genres from cleaned input
        genres_input = self.cleaned_data.get('genres_input', '')
        instance.genres = genres_input
        
        if commit:
            instance.save()
        
        return instance


class UserProfileForm(forms.ModelForm):
    """
    Form for user profile settings.
    
    Demonstrates: ModelForm, multi-select, form processing
    """
    
    GENRE_CHOICES = [
        ('action', 'Action'),
        ('comedy', 'Comedy'),
        ('drama', 'Drama'),
        ('horror', 'Horror'),
        ('sci-fi', 'Sci-Fi'),
        ('romance', 'Romance'),
        ('thriller', 'Thriller'),
        ('documentary', 'Documentary'),
        ('animation', 'Animation'),
        ('fantasy', 'Fantasy'),
    ]
    
    favorite_genres_select = forms.MultipleChoiceField(
        required=False,
        choices=GENRE_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'genre-checkbox'}),
        label='Favorite Genres'
    )
    
    class Meta:
        model = UserProfile
        fields = ['bio']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Tell us about yourself...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pre-select existing favorite genres
        if self.instance and self.instance.pk:
            current_genres = self.instance.get_favorite_genres_list()
            # Convert to lowercase for matching
            self.initial['favorite_genres_select'] = [
                g.lower() for g in current_genres
            ]
    
    def save(self, commit=True):
        """
        Save profile with genre handling.
        
        Demonstrates: List processing, string operations
        """
        instance = super().save(commit=False)
        
        # Get selected genres (list of lowercase strings)
        selected = self.cleaned_data.get('favorite_genres_select', [])
        
        # Convert to title case and join
        genres_str = ', '.join([g.title() for g in selected])
        instance.favorite_genres = genres_str
        
        if commit:
            instance.save()
        
        return instance


class QuickRatingForm(forms.Form):
    """
    Quick rating form without review.
    
    Demonstrates: Simple non-model form, casting
    """
    
    movie_id = forms.IntegerField(widget=forms.HiddenInput())
    stars = forms.FloatField(
        min_value=0.5,
        max_value=5.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.5',
            'min': '0.5',
            'max': '5'
        })
    )
    
    def clean_movie_id(self):
        """
        Validate movie exists.
        
        Demonstrates: Casting, Django ORM query, if/else
        """
        movie_id = self.cleaned_data.get('movie_id')
        
        # Casting to int (may be string from form)
        movie_id = int(movie_id)
        
        # Check if movie exists
        if not Movie.objects.filter(pk=movie_id).exists():
            raise forms.ValidationError("Movie not found")
        
        return movie_id
