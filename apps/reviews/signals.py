from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.db.models import Model

from apps.abstract.redis_storage import cache_delete_pattern
from apps.reviews.models import Review


@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def invalidate_hotel_review_lists(
    sender: type[Model], **kwargs: object
) -> None:
    """Clear cached hotel review lists whenever reviews change."""
    cache_delete_pattern("reviews:hotel:list:*")
