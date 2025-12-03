"""
Management command to add sample movies for testing external API integrations.
"""

from django.core.management.base import BaseCommand
from movies.models import Movie


class Command(BaseCommand):
    help = 'Add sample movies with real titles for testing IMDB/Letterboxd integrations'

    def handle(self, *args, **options):
        sample_movies = [
            {
                'title': 'The Shawshank Redemption',
                'year': 1994,
                'genres': 'Drama',
                'overview': 'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.',
                'popularity': 95.0,
            },
            {
                'title': 'The Godfather',
                'year': 1972,
                'genres': 'Crime, Drama',
                'overview': 'The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant youngest son.',
                'popularity': 93.0,
            },
            {
                'title': 'The Dark Knight',
                'year': 2008,
                'genres': 'Action, Crime, Drama',
                'overview': 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.',
                'popularity': 92.0,
            },
            {
                'title': 'Pulp Fiction',
                'year': 1994,
                'genres': 'Crime, Drama',
                'overview': 'The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.',
                'popularity': 91.0,
            },
            {
                'title': 'Inception',
                'year': 2010,
                'genres': 'Action, Adventure, Sci-Fi',
                'overview': 'A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.',
                'popularity': 90.0,
            },
            {
                'title': 'Interstellar',
                'year': 2014,
                'genres': 'Adventure, Drama, Sci-Fi',
                'overview': 'A team of explorers travel through a wormhole in space in an attempt to ensure humanity\'s survival.',
                'popularity': 89.0,
            },
            {
                'title': 'Parasite',
                'year': 2019,
                'genres': 'Comedy, Drama, Thriller',
                'overview': 'Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.',
                'popularity': 88.0,
            },
            {
                'title': 'Spirited Away',
                'year': 2001,
                'genres': 'Animation, Adventure, Family',
                'overview': 'During her family\'s move to the suburbs, a sullen 10-year-old girl wanders into a world ruled by gods, witches, and spirits, and where humans are changed into beasts.',
                'popularity': 87.0,
            },
        ]

        created_count = 0
        updated_count = 0

        for movie_data in sample_movies:
            movie, created = Movie.objects.update_or_create(
                title=movie_data['title'],
                year=movie_data['year'],
                defaults={
                    'genres': movie_data['genres'],
                    'overview': movie_data['overview'],
                    'popularity': movie_data['popularity'],
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {movie.title} ({movie.year})'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated: {movie.title} ({movie.year})'))

        self.stdout.write(self.style.SUCCESS(f'\nDone! Created {created_count} new movies, updated {updated_count} existing.'))
