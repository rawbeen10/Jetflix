from django.core.management.base import BaseCommand
from movies.models import Review, WatchHistory, Watchlist, UserInteraction

class Command(BaseCommand):
    help = 'Populate UserInteraction data from existing reviews, watch history, and watchlists'

    def handle(self, *args, **options):
        self.stdout.write('Populating interaction data...')
        
        # Create interactions from reviews
        reviews = Review.objects.all()
        review_count = 0
        for review in reviews:
            interaction, created = UserInteraction.objects.get_or_create(
                user=review.user,
                movie=review.movie,
                interaction_type='review',
                defaults={'score': float(review.rating)}
            )
            if created:
                review_count += 1
        
        # Create interactions from watch history
        watch_history = WatchHistory.objects.all()
        watch_count = 0
        for watch in watch_history:
            interaction, created = UserInteraction.objects.get_or_create(
                user=watch.user,
                movie=watch.movie,
                interaction_type='watch',
                defaults={'score': 2.0}
            )
            if created:
                watch_count += 1
        
        # Create interactions from watchlists
        watchlists = Watchlist.objects.all()
        watchlist_count = 0
        for watchlist_item in watchlists:
            interaction, created = UserInteraction.objects.get_or_create(
                user=watchlist_item.user,
                movie=watchlist_item.movie,
                interaction_type='watchlist',
                defaults={'score': 1.0}
            )
            if created:
                watchlist_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {review_count} review interactions, '
                f'{watch_count} watch interactions, and '
                f'{watchlist_count} watchlist interactions'
            )
        )