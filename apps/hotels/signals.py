from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.abstract.redis_storage import build_cache_key, cache_delete, cache_delete_pattern
from apps.hotels.models import Hotel


@receiver(post_save, sender=Hotel)
@receiver(post_delete, sender=Hotel)
def invalidate_hotel_cache(sender, instance: Hotel, **kwargs) -> None:
    """Clear hotel detail and list caches when a hotel changes."""
    cache_delete(build_cache_key("hotels:detail", instance.pk))
    cache_delete_pattern("hotels:list:*")
