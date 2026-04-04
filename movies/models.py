from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.utils import timezone
from collections import defaultdict
import math


class Language(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Movie(models.Model):
    id           = models.AutoField(primary_key=True)
    title        = models.CharField(max_length=255)
    year         = models.IntegerField()
    description  = models.TextField()
    thumbnail    = models.ImageField(upload_to='thumbnails/')
    video        = models.FileField(upload_to='movies/')
    genres       = models.ManyToManyField(Genre, related_name='movies')
    language     = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True, related_name='movies')
    cast         = models.CharField(max_length=255, default='Unknown')
    movie_length = models.CharField(max_length=20, default='Unknown')
    review_stars = models.FloatField(default=0.0)
    views        = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def get_genres_display(self):
        return ", ".join([genre.name for genre in self.genres.all()])

    def update_average_rating(self):
        avg_rating = self.reviews.aggregate(Avg('rating'))['rating__avg']
        self.review_stars = avg_rating if avg_rating else 0.0
        self.save(update_fields=['review_stars'])

    # -------------------------------------------------------------------------
    # CONTENT-BASED (movie-to-movie similarity, used inside modal)
    # -------------------------------------------------------------------------

    def _get_content_vector(self):
        genre_ids   = set(self.genres.values_list('id', flat=True))
        language_id = {self.language_id} if self.language_id else set()
        cast_set    = set(
            actor.strip().lower()
            for actor in self.cast.split(',')
            if actor.strip() and actor.strip().lower() != 'unknown'
        )
        return {'genres': genre_ids, 'language': language_id, 'cast': cast_set}

    def _content_similarity_score(self, other):
        a = self._get_content_vector()
        b = other._get_content_vector()

        def jaccard(set_a, set_b):
            union = set_a | set_b
            if not union:
                return 0.0
            return len(set_a & set_b) / len(union)

        return (
            0.5 * jaccard(a['genres'],   b['genres']) +
            0.2 * jaccard(a['language'], b['language']) +
            0.3 * jaccard(a['cast'],     b['cast'])
        )

    def get_content_based_similar_movies(self, limit=6):
        candidates = Movie.objects.filter(
            is_published=True
        ).exclude(id=self.id).prefetch_related('genres')

        scored = []
        for candidate in candidates:
            score = self._content_similarity_score(candidate)
            if score > 0:
                scored.append((candidate, score))

        scored.sort(key=lambda x: (x[1], x[0].review_stars), reverse=True)
        return [movie for movie, _ in scored[:limit]]

    def get_similar_movies(self, limit=6):
        movie_user_ids = set(self.interactions.values_list('user_id', flat=True).distinct())

        if not movie_user_ids:
            return self.get_content_based_similar_movies(limit=limit)

        candidate_movies = Movie.objects.filter(
            is_published=True
        ).exclude(id=self.id).prefetch_related('interactions')

        similarities = []
        for candidate in candidate_movies:
            candidate_user_ids = set(candidate.interactions.values_list('user_id', flat=True).distinct())
            union = movie_user_ids | candidate_user_ids
            if union:
                jaccard = len(movie_user_ids & candidate_user_ids) / len(union)
                if jaccard > 0:
                    similarities.append((candidate, jaccard))

        similarities.sort(key=lambda x: (x[1], x[0].review_stars), reverse=True)
        result = [movie for movie, _ in similarities[:limit]]

        if len(result) < limit:
            existing_ids = {self.id} | {m.id for m in result}
            for movie in self.get_content_based_similar_movies(limit=limit):
                if movie.id not in existing_ids:
                    result.append(movie)
                    existing_ids.add(movie.id)
                if len(result) >= limit:
                    break

        return result

    # -------------------------------------------------------------------------
    # CONTENT-BASED RECOMMENDATIONS (user profile, used on homepage)
    # -------------------------------------------------------------------------

    @classmethod
    def get_content_based_recommendations(cls, user, limit=6, min_interactions=2):
        user_interactions = list(
            user.interactions.select_related('movie').prefetch_related(
                'movie__genres'
            ).order_by('-created_at')
        )

        if len(user_interactions) < min_interactions:
            return list(
                cls.objects.filter(
                    is_published=True
                ).order_by('-review_stars', '-views')[:limit]
            )

        user_movie_ids = {i.movie_id for i in user_interactions}

        now = timezone.now()

        user_genres    = defaultdict(float)
        user_languages = defaultdict(float)
        user_cast      = defaultdict(float)

        type_weight_map = {
            'watch':     2.0,
            'review':    1.5,
            'watchlist': 1.0,
        }

        for interaction in user_interactions:
            movie          = interaction.movie
            days_ago       = max((now - interaction.created_at).days, 0)
            recency_weight = math.exp(-0.023 * days_ago)
            type_weight    = type_weight_map.get(interaction.interaction_type, 1.0)
            final_weight   = recency_weight * type_weight

            for genre_id in movie.genres.values_list('id', flat=True):
                user_genres[genre_id] += final_weight

            if movie.language_id:
                user_languages[movie.language_id] += final_weight

            for actor in movie.cast.split(','):
                actor = actor.strip().lower()
                if actor and actor != 'unknown':
                    user_cast[actor] += final_weight

        def weighted_similarity(user_profile_dict, candidate_set):
            if not user_profile_dict or not candidate_set:
                return 0.0
            total = sum(user_profile_dict.values())
            if total == 0:
                return 0.0
            matched = sum(user_profile_dict.get(f, 0.0) for f in candidate_set)
            return matched / total

        candidates = cls.objects.filter(
            is_published=True
        ).exclude(
            id__in=user_movie_ids
        ).select_related('language').prefetch_related('genres')

        scored = []
        for candidate in candidates:
            candidate_genres = set(candidate.genres.values_list('id', flat=True))
            candidate_lang   = {candidate.language_id} if candidate.language_id else set()
            candidate_cast   = {
                actor.strip().lower()
                for actor in candidate.cast.split(',')
                if actor.strip() and actor.strip().lower() != 'unknown'
            }

            genre_score    = weighted_similarity(user_genres,    candidate_genres)
            language_score = weighted_similarity(user_languages, candidate_lang)
            cast_score     = weighted_similarity(user_cast,      candidate_cast)

            total_score = (0.5 * genre_score) + (0.2 * language_score) + (0.3 * cast_score)

            if total_score > 0:
                scored.append((candidate, total_score))

        scored.sort(key=lambda x: (x[1], x[0].review_stars), reverse=True)
        return [movie for movie, _ in scored[:limit]]

    # -------------------------------------------------------------------------
    # COLLABORATIVE FILTERING (user-based Jaccard, used on homepage)
    # -------------------------------------------------------------------------

    @classmethod
    def get_recommendations_for_user(cls, user, limit=6):
        user_movies = set(user.interactions.values_list('movie_id', flat=True).distinct())

        if not user_movies:
            return list(
                cls.objects.filter(
                    is_published=True
                ).order_by('-views', '-review_stars')[:limit]
            )

        all_other_users = User.objects.exclude(id=user.id).prefetch_related('interactions')

        similarities = []
        for other_user in all_other_users:
            other_movies = set(other_user.interactions.values_list('movie_id', flat=True).distinct())
            union = user_movies | other_movies
            if union:
                jaccard = len(user_movies & other_movies) / len(union)
                if jaccard > 0:
                    similarities.append((other_user, jaccard))

        if not similarities:
            return list(cls.get_content_based_recommendations(user, limit=limit, min_interactions=1))

        similarities.sort(key=lambda x: x[1], reverse=True)
        top_similar_users = [u for u, _ in similarities[:20]]

        movie_scores   = defaultdict(float)
        user_score_map = {u.id: score for u, score in similarities[:20]}

        for other_user in top_similar_users:
            other_movies = set(other_user.interactions.values_list('movie_id', flat=True).distinct())
            for movie_id in other_movies - user_movies:
                movie_scores[movie_id] += user_score_map[other_user.id]

        if not movie_scores:
            return list(cls.get_content_based_recommendations(user, limit=limit, min_interactions=1))

        sorted_movie_ids = sorted(movie_scores, key=lambda mid: movie_scores[mid], reverse=True)

        movies_by_id = {
            m.id: m for m in cls.objects.filter(
                id__in=sorted_movie_ids,
                is_published=True
            ).select_related('language').prefetch_related('genres')
        }

        recommended_movies = [
            movies_by_id[mid] for mid in sorted_movie_ids if mid in movies_by_id
        ][:limit]

        if len(recommended_movies) < limit:
            existing_ids = user_movies | {m.id for m in recommended_movies}
            for movie in cls.get_content_based_recommendations(user, limit=limit, min_interactions=1):
                if movie.id not in existing_ids:
                    recommended_movies.append(movie)
                    existing_ids.add(movie.id)
                if len(recommended_movies) >= limit:
                    break

        return recommended_movies


class Watchlist(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    movie    = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='watchlisted_by')
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering        = ['-added_on']

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"


class Favorite(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    movie    = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='favorited_by')
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering        = ['-added_on']

    def __str__(self):
        return f"{self.user.username} ♥ {self.movie.title}"


class Review(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    movie       = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    rating      = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField()
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering        = ['-created_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.movie.update_average_rating()

    def delete(self, *args, **kwargs):
        movie = self.movie
        super().delete(*args, **kwargs)
        movie.update_average_rating()

    def time_since_created(self):
        now  = timezone.now()
        diff = now - self.created_at
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} min{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"


class WatchHistory(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_history')
    movie      = models.ForeignKey('Movie', on_delete=models.CASCADE)
    watched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['-watched_at']
        verbose_name_plural = 'Watch Histories'
        unique_together     = ('user', 'movie')

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"


class UserInteraction(models.Model):
    INTERACTION_TYPES = [
        ('watch',     'Watched'),
        ('review',    'Reviewed'),
        ('watchlist', 'Added to Watchlist'),
    ]

    user             = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactions')
    movie            = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    score            = models.FloatField(default=1.0)
    created_at       = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.movie.title} ({self.interaction_type})"