#!/usr/bin/env python
"""
CineSense Tkinter GUI Client
=============================

Demonstrates:
- Tkinter GUI creation
- Classes with __init__ methods
- Methods and self
- Callbacks and event handling
- f-strings for dynamic labels
- Collections (list, dict)
- For loops for widget creation
- If/else conditional logic
- String modification
- Casting between types

Usage:
    python tkinter_client/main.py

Run from the cinesense_project directory after setting up Django.
"""

import os
import sys

# Setup path and Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinesense_project.settings')

import django
django.setup()

# Tkinter imports
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import List, Dict, Optional, Callable

# Django imports
from movies.models import Movie, Rating, UserProfile
from django.contrib.auth.models import User
from django.db.models import Avg, Count


class CineSenseApp:
    """
    Main application class for CineSense GUI.
    
    Demonstrates: Classes, __init__, self, Tkinter root window
    """
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the application.
        
        Demonstrates: __init__ method, self, Tkinter setup,
                     f-strings for window title
        """
        self.root = root
        self.root.title("🎬 CineSense - Movie Recommendation System")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Current user - None initially
        self.current_user: Optional[User] = None
        
        # Style configuration
        self.style = ttk.Style()
        self.style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
        self.style.configure('Heading.TLabel', font=('Helvetica', 12, 'bold'))
        
        # Initialize UI
        self._create_menu()
        self._create_main_frame()
        self._show_home()
    
    def _create_menu(self) -> None:
        """
        Create menu bar.
        
        Demonstrates: Tkinter Menu, callbacks
        """
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Home", command=self._show_home)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Movies menu
        movies_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Movies", menu=movies_menu)
        movies_menu.add_command(label="Browse Movies", command=self._show_movies)
        movies_menu.add_command(label="Add Movie", command=self._show_add_movie)
        movies_menu.add_command(label="Search", command=self._show_search)
        
        # User menu
        user_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="User", menu=user_menu)
        user_menu.add_command(label="Login/Switch User", command=self._show_login)
        user_menu.add_command(label="My Ratings", command=self._show_my_ratings)
        user_menu.add_command(label="Statistics", command=self._show_statistics)
    
    def _create_main_frame(self) -> None:
        """
        Create main content frame.
        
        Demonstrates: Tkinter Frame, pack geometry
        """
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status bar at bottom
        self.status_var = tk.StringVar(value="Welcome to CineSense!")
        self.status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding="5"
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _clear_frame(self) -> None:
        """
        Clear all widgets from main frame.
        
        Demonstrates: For loop over widgets, widget destruction
        """
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def _update_status(self, message: str) -> None:
        """
        Update status bar.
        
        Demonstrates: f-strings, StringVar
        """
        user_info = f" | User: {self.current_user.username}" if self.current_user else ""
        self.status_var.set(f"{message}{user_info}")
    
    # =========================================================
    # View Methods
    # =========================================================
    
    def _show_home(self) -> None:
        """
        Show home screen.
        
        Demonstrates: Tkinter widgets, callbacks, f-strings
        """
        self._clear_frame()
        self._update_status("Home")
        
        # Title
        title_label = ttk.Label(
            self.main_frame,
            text="🎬 CineSense",
            style='Title.TLabel'
        )
        title_label.pack(pady=20)
        
        # Stats frame
        stats_frame = ttk.LabelFrame(self.main_frame, text="Statistics", padding="10")
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Get counts
        movie_count = Movie.objects.count()
        rating_count = Rating.objects.count()
        user_count = User.objects.count()
        
        # Display stats using f-strings
        ttk.Label(stats_frame, text=f"📽️ Movies: {movie_count}").pack(side=tk.LEFT, padx=20)
        ttk.Label(stats_frame, text=f"⭐ Ratings: {rating_count}").pack(side=tk.LEFT, padx=20)
        ttk.Label(stats_frame, text=f"👥 Users: {user_count}").pack(side=tk.LEFT, padx=20)
        
        # Quick actions frame
        actions_frame = ttk.LabelFrame(self.main_frame, text="Quick Actions", padding="10")
        actions_frame.pack(fill=tk.X, pady=10)
        
        # Action buttons - list of tuples
        actions = [
            ("Browse Movies", self._show_movies),
            ("Add Movie", self._show_add_movie),
            ("Search", self._show_search),
            ("My Ratings", self._show_my_ratings),
        ]
        
        # For loop to create buttons
        for text, command in actions:
            ttk.Button(
                actions_frame,
                text=text,
                command=command,
                width=15
            ).pack(side=tk.LEFT, padx=5)
        
        # Recent movies
        self._show_recent_movies()
    
    def _show_recent_movies(self) -> None:
        """
        Display recent movies in home view.
        
        Demonstrates: Django ORM, for loop, f-strings
        """
        recent_frame = ttk.LabelFrame(self.main_frame, text="Recent Movies", padding="10")
        recent_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Get recent movies
        recent_movies = Movie.objects.order_by('-created_at')[:10]
        
        # Create treeview for display
        columns = ('title', 'year', 'genres', 'rating')
        tree = ttk.Treeview(recent_frame, columns=columns, show='headings', height=8)
        
        # Configure columns
        tree.heading('title', text='Title')
        tree.heading('year', text='Year')
        tree.heading('genres', text='Genres')
        tree.heading('rating', text='Rating')
        
        tree.column('title', width=250)
        tree.column('year', width=60)
        tree.column('genres', width=200)
        tree.column('rating', width=80)
        
        # Insert data using for loop
        for movie in recent_movies:
            avg = movie.average_rating
            rating_str = f"★{avg:.1f}" if avg > 0 else "No ratings"
            
            tree.insert('', tk.END, values=(
                movie.title,
                movie.year,
                movie.genres[:30] + "..." if len(movie.genres) > 30 else movie.genres,
                rating_str,
            ))
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(recent_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
    
    def _show_movies(self) -> None:
        """
        Show movie browser.
        
        Demonstrates: Tkinter Treeview, pagination, callbacks
        """
        self._clear_frame()
        self._update_status("Browse Movies")
        
        ttk.Label(
            self.main_frame,
            text="📽️ Browse Movies",
            style='Title.TLabel'
        ).pack(pady=10)
        
        # Filter frame
        filter_frame = ttk.Frame(self.main_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Filter by genre:").pack(side=tk.LEFT)
        
        # Genre dropdown
        genres = ['All'] + sorted(set(
            g.strip().title()
            for m in Movie.objects.all()
            for g in m.genres.split(',')
            if g.strip()
        ))
        
        self.genre_var = tk.StringVar(value='All')
        genre_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.genre_var,
            values=genres,
            state='readonly',
            width=20
        )
        genre_combo.pack(side=tk.LEFT, padx=5)
        genre_combo.bind('<<ComboboxSelected>>', lambda e: self._refresh_movie_list())
        
        # Movies treeview
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        columns = ('id', 'title', 'year', 'genres', 'rating', 'count')
        self.movie_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        # Configure columns
        self.movie_tree.heading('id', text='ID')
        self.movie_tree.heading('title', text='Title')
        self.movie_tree.heading('year', text='Year')
        self.movie_tree.heading('genres', text='Genres')
        self.movie_tree.heading('rating', text='Avg Rating')
        self.movie_tree.heading('count', text='# Ratings')
        
        self.movie_tree.column('id', width=50)
        self.movie_tree.column('title', width=250)
        self.movie_tree.column('year', width=60)
        self.movie_tree.column('genres', width=200)
        self.movie_tree.column('rating', width=80)
        self.movie_tree.column('count', width=70)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.movie_tree.yview)
        self.movie_tree.configure(yscrollcommand=scrollbar.set)
        
        self.movie_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click to rate
        self.movie_tree.bind('<Double-1>', self._on_movie_double_click)
        
        # Populate list
        self._refresh_movie_list()
    
    def _refresh_movie_list(self) -> None:
        """
        Refresh movie list based on filter.
        
        Demonstrates: Django ORM filtering, for loop
        """
        # Clear existing items
        for item in self.movie_tree.get_children():
            self.movie_tree.delete(item)
        
        # Get filter
        genre_filter = self.genre_var.get()
        
        # Query movies
        movies = Movie.objects.annotate(
            avg_rating=Avg('ratings__stars'),
            num_ratings=Count('ratings')
        )
        
        # Apply filter if not 'All'
        if genre_filter != 'All':
            movies = movies.filter(genres__icontains=genre_filter)
        
        movies = movies.order_by('-avg_rating', '-rating_count')[:100]
        
        # Insert data
        for movie in movies:
            avg = movie.avg_rating or 0
            rating_str = f"{avg:.2f}" if avg > 0 else "-"
            
            self.movie_tree.insert('', tk.END, values=(
                movie.pk,
                movie.title,
                movie.year,
                movie.genres[:30],
                rating_str,
                movie.rating_count,
            ), tags=(str(movie.pk),))
    
    def _on_movie_double_click(self, event) -> None:
        """
        Handle double-click on movie.
        
        Demonstrates: Event handling, callbacks
        """
        selection = self.movie_tree.selection()
        if selection:
            item = self.movie_tree.item(selection[0])
            movie_id = item['values'][0]
            self._show_rate_movie(movie_id)
    
    def _show_add_movie(self) -> None:
        """
        Show add movie form.
        
        Demonstrates: Tkinter Entry, form handling, callbacks
        """
        self._clear_frame()
        self._update_status("Add New Movie")
        
        ttk.Label(
            self.main_frame,
            text="➕ Add New Movie",
            style='Title.TLabel'
        ).pack(pady=10)
        
        # Form frame
        form_frame = ttk.Frame(self.main_frame, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields - dict of field configs
        fields = {
            'title': {'label': 'Title *', 'required': True},
            'year': {'label': 'Year *', 'required': True},
            'genres': {'label': 'Genres (comma-separated)', 'required': False},
            'overview': {'label': 'Overview', 'required': False, 'multiline': True},
            'popularity': {'label': 'Popularity', 'required': False, 'default': '0'},
        }
        
        self.form_vars = {}  # dict to store form variables
        
        # For loop to create form fields
        row = 0
        for field_name, config in fields.items():
            ttk.Label(form_frame, text=config['label']).grid(
                row=row, column=0, sticky=tk.W, pady=5
            )
            
            if config.get('multiline'):
                # Text widget for multiline
                text_widget = scrolledtext.ScrolledText(
                    form_frame, height=4, width=50
                )
                text_widget.grid(row=row, column=1, pady=5, sticky=tk.W)
                self.form_vars[field_name] = text_widget
            else:
                # Entry widget
                var = tk.StringVar(value=config.get('default', ''))
                entry = ttk.Entry(form_frame, textvariable=var, width=50)
                entry.grid(row=row, column=1, pady=5, sticky=tk.W)
                self.form_vars[field_name] = var
            
            row += 1
        
        # Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=row, column=1, pady=20, sticky=tk.W)
        
        ttk.Button(btn_frame, text="Save", command=self._save_movie).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self._show_home).pack(side=tk.LEFT, padx=5)
    
    def _save_movie(self) -> None:
        """
        Save new movie from form.
        
        Demonstrates: Form validation, casting, Django ORM, if/else, f-strings
        """
        # Get values
        title = self.form_vars['title'].get().strip()
        year_str = self.form_vars['year'].get().strip()
        genres = self.form_vars['genres'].get().strip()
        overview = self.form_vars['overview'].get('1.0', tk.END).strip()
        popularity_str = self.form_vars['popularity'].get().strip()
        
        # Validation with if/else
        if not title:
            messagebox.showerror("Error", "Title is required!")
            return
        
        # Cast year to int
        try:
            year = int(year_str)  # Casting
            if year < 1888 or year > 2100:
                raise ValueError("Invalid year")
        except ValueError:
            messagebox.showerror("Error", "Year must be a valid number (1888-2100)")
            return
        
        # Cast popularity to float
        try:
            popularity = float(popularity_str) if popularity_str else 0.0
        except ValueError:
            popularity = 0.0
        
        # Create movie using Django ORM
        movie = Movie.objects.create(
            title=title,
            year=year,
            genres=genres,
            overview=overview,
            popularity=popularity,
        )
        
        # Success message with f-string
        messagebox.showinfo(
            "Success",
            f"Movie '{movie.title}' ({movie.year}) added successfully!"
        )
        
        self._show_home()
    
    def _show_search(self) -> None:
        """
        Show search interface.
        
        Demonstrates: Tkinter Entry, callbacks, string operations
        """
        self._clear_frame()
        self._update_status("Search Movies")
        
        ttk.Label(
            self.main_frame,
            text="🔍 Search Movies",
            style='Title.TLabel'
        ).pack(pady=10)
        
        # Search frame
        search_frame = ttk.Frame(self.main_frame)
        search_frame.pack(fill=tk.X, pady=10)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<Return>', lambda e: self._do_search())
        
        ttk.Button(search_frame, text="Search", command=self._do_search).pack(side=tk.LEFT)
        
        # Results frame
        self.results_frame = ttk.Frame(self.main_frame)
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    def _do_search(self) -> None:
        """
        Perform search.
        
        Demonstrates: String operations, Django ORM Q objects, for loop
        """
        from django.db.models import Q
        
        # Clear results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        query = self.search_var.get().strip().lower()  # String modification
        
        if len(query) < 2:
            ttk.Label(self.results_frame, text="Please enter at least 2 characters").pack()
            return
        
        # Search using Q objects
        movies = Movie.objects.filter(
            Q(title__icontains=query) |
            Q(genres__icontains=query) |
            Q(overview__icontains=query)
        ).annotate(avg_rating=Avg('ratings__stars'))[:20]
        
        # Display results
        if not movies:
            ttk.Label(
                self.results_frame,
                text=f"No movies found matching '{query}'"
            ).pack()
            return
        
        ttk.Label(
            self.results_frame,
            text=f"Found {movies.count()} result(s) for '{query}':",
            style='Heading.TLabel'
        ).pack(anchor=tk.W, pady=5)
        
        # For loop to display results
        for movie in movies:
            frame = ttk.Frame(self.results_frame)
            frame.pack(fill=tk.X, pady=2)
            
            avg = movie.avg_rating or 0
            rating_str = f"★{avg:.1f}" if avg > 0 else "No ratings"
            
            # f-string for display
            text = f"{movie.title} ({movie.year}) - {movie.genres[:30]} - {rating_str}"
            ttk.Label(frame, text=text).pack(side=tk.LEFT)
            
            ttk.Button(
                frame,
                text="Rate",
                command=lambda m=movie: self._show_rate_movie(m.pk)
            ).pack(side=tk.RIGHT)
    
    def _show_login(self) -> None:
        """
        Show login dialog.
        
        Demonstrates: Tkinter Toplevel dialog, callbacks
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Login / Switch User")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Enter username:").pack(pady=10)
        
        username_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=username_var, width=30)
        entry.pack(pady=5)
        entry.focus()
        
        def do_login():
            username = username_var.get().strip()
            if username:
                user, created = User.objects.get_or_create(username=username)
                self.current_user = user
                
                if created:
                    messagebox.showinfo("Welcome", f"New user '{username}' created!")
                else:
                    rating_count = Rating.objects.filter(user=user).count()
                    messagebox.showinfo(
                        "Welcome Back",
                        f"Welcome back, {username}! You have {rating_count} ratings."
                    )
                
                dialog.destroy()
                self._update_status("Logged in")
        
        entry.bind('<Return>', lambda e: do_login())
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Login", command=do_login).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)
    
    def _show_rate_movie(self, movie_id: int) -> None:
        """
        Show rating dialog for a movie.
        
        Demonstrates: Toplevel dialog, Scale widget, callbacks
        """
        if not self.current_user:
            if messagebox.askyesno("Login Required", "You need to login to rate. Login now?"):
                self._show_login()
            return
        
        try:
            movie = Movie.objects.get(pk=movie_id)
        except Movie.DoesNotExist:
            messagebox.showerror("Error", "Movie not found")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Rate: {movie.title}")
        dialog.geometry("400x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Movie info
        ttk.Label(
            dialog,
            text=f"🎬 {movie.title}",
            style='Heading.TLabel'
        ).pack(pady=10)
        
        ttk.Label(dialog, text=f"Year: {movie.year}").pack()
        ttk.Label(dialog, text=f"Genres: {movie.genres}").pack()
        
        # Check for existing rating
        existing = Rating.objects.filter(user=self.current_user, movie=movie).first()
        
        # Rating scale
        ttk.Label(dialog, text="\nYour Rating:").pack()
        
        rating_var = tk.DoubleVar(value=existing.stars if existing else 3.0)
        scale = ttk.Scale(
            dialog,
            from_=0.5,
            to=5.0,
            variable=rating_var,
            orient=tk.HORIZONTAL,
            length=300
        )
        scale.pack(pady=5)
        
        rating_label = ttk.Label(dialog, text="3.0 ★")
        rating_label.pack()
        
        def update_label(*args):
            val = rating_var.get()
            rating_label.config(text=f"{val:.1f} ★")
        
        rating_var.trace_add('write', update_label)
        
        # Tags
        ttk.Label(dialog, text="\nTags (comma-separated):").pack()
        tags_var = tk.StringVar(value=existing.tags if existing else "")
        ttk.Entry(dialog, textvariable=tags_var, width=40).pack(pady=5)
        
        def save_rating():
            stars = round(rating_var.get() * 2) / 2  # Round to 0.5
            tags = tags_var.get().strip()
            
            if existing:
                existing.stars = stars
                existing.tags = tags
                existing.save()
                messagebox.showinfo("Updated", f"Rating updated to {stars:.1f}★")
            else:
                Rating.objects.create(
                    user=self.current_user,
                    movie=movie,
                    stars=stars,
                    tags=tags,
                )
                messagebox.showinfo("Saved", f"Rated '{movie.title}' {stars:.1f}★")
            
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Save", command=save_rating).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)
    
    def _show_my_ratings(self) -> None:
        """
        Show current user's ratings.
        
        Demonstrates: Django ORM, for loop, f-strings
        """
        if not self.current_user:
            messagebox.showinfo("Login Required", "Please login first")
            self._show_login()
            return
        
        self._clear_frame()
        self._update_status(f"My Ratings - {self.current_user.username}")
        
        ttk.Label(
            self.main_frame,
            text=f"⭐ Ratings by {self.current_user.username}",
            style='Title.TLabel'
        ).pack(pady=10)
        
        # Get ratings
        ratings = Rating.objects.filter(
            user=self.current_user
        ).select_related('movie').order_by('-created_at')
        
        if not ratings:
            ttk.Label(
                self.main_frame,
                text="You haven't rated any movies yet!"
            ).pack(pady=20)
            return
        
        # Stats
        stats_frame = ttk.Frame(self.main_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        
        avg_rating = sum(r.stars for r in ratings) / len(ratings)
        ttk.Label(
            stats_frame,
            text=f"Total: {len(ratings)} | Average: {avg_rating:.2f}★"
        ).pack()
        
        # Ratings list
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('movie', 'year', 'rating', 'tags', 'date')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        tree.heading('movie', text='Movie')
        tree.heading('year', text='Year')
        tree.heading('rating', text='Rating')
        tree.heading('tags', text='Tags')
        tree.heading('date', text='Date')
        
        tree.column('movie', width=250)
        tree.column('year', width=60)
        tree.column('rating', width=80)
        tree.column('tags', width=150)
        tree.column('date', width=100)
        
        for rating in ratings:
            tree.insert('', tk.END, values=(
                rating.movie.title,
                rating.movie.year,
                f"{rating.stars:.1f}★",
                rating.tags[:20],
                rating.created_at.strftime('%Y-%m-%d'),
            ))
        
        tree.pack(fill=tk.BOTH, expand=True)
    
    def _show_statistics(self) -> None:
        """
        Show statistics view.
        
        Demonstrates: Data aggregation, for loop, dict operations
        """
        self._clear_frame()
        self._update_status("Statistics")
        
        ttk.Label(
            self.main_frame,
            text="📊 Statistics",
            style='Title.TLabel'
        ).pack(pady=10)
        
        # Overall stats
        stats_frame = ttk.LabelFrame(self.main_frame, text="Overall", padding="10")
        stats_frame.pack(fill=tk.X, pady=10)
        
        movie_count = Movie.objects.count()
        rating_count = Rating.objects.count()
        user_count = User.objects.count()
        
        ttk.Label(stats_frame, text=f"Movies: {movie_count}").grid(row=0, column=0, padx=20)
        ttk.Label(stats_frame, text=f"Ratings: {rating_count}").grid(row=0, column=1, padx=20)
        ttk.Label(stats_frame, text=f"Users: {user_count}").grid(row=0, column=2, padx=20)
        
        # Genre distribution
        genre_frame = ttk.LabelFrame(self.main_frame, text="Top Genres", padding="10")
        genre_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Count genres using dict
        genre_counts = {}
        for movie in Movie.objects.all():
            for genre in movie.get_genres_list():
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Sort using lambda
        sorted_genres = sorted(
            genre_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Display using for loop
        for i, (genre, count) in enumerate(sorted_genres):
            ttk.Label(
                genre_frame,
                text=f"{i+1}. {genre}: {count} movies"
            ).pack(anchor=tk.W)


def main():
    """
    Main entry point.
    
    Demonstrates: Tkinter main loop
    """
    root = tk.Tk()
    app = CineSenseApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
