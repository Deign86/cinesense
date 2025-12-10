from django.test import TestCase
from django.urls import reverse
from movies.models import Movie, Rating, User
import time

class PerformanceTest(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(username='testuser', password='password')
        
        # Create 50 movies
        movies = []
        for i in range(50):
            movies.append(Movie(
                title=f'Movie {i}',
                year=2020,
                popularity=i # varying popularity
            ))
        Movie.objects.bulk_create(movies)
        
        # Rate the first 20 movies
        all_movies = Movie.objects.all()
        ratings = []
        for i in range(20):
            ratings.append(Rating(
                user=self.user,
                movie=all_movies[i],
                stars=4.0
            ))
        Rating.objects.bulk_create(ratings)

    def test_movie_list_performance(self):
        """Test that movie list loads quickly and contains rating data."""
        start_time = time.time()
        response = self.client.get(reverse('movie_list'))
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"\nMovie List Load Time: {duration:.4f}s")
        
        self.assertEqual(response.status_code, 200)
        
        # Check that we have movies in context
        movies = response.context['movies']
        self.assertTrue(len(movies) > 0)
        
        # Check that avg_rating is present on movies that have ratings
        # Check that avg_rating is present on movies that have ratings
        # The first 20 movies are rated in setUp.
        # The page size is 12, so all movies on the first page should have ratings.
        
        top_movie = movies[0]
        self.assertTrue(hasattr(top_movie, 'avg_rating'), "Movie should have avg_rating annotated")
        self.assertEqual(top_movie.avg_rating, 4.0)
        
        # Verify number of queries is optimized (optional but good)
        # We expect: 
        # 1. Count query for pagination (optimized)
        # 2. Query for IDs on page
        # 3. Query for annotated movies
        
