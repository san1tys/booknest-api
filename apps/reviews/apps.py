from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    """App configuration for reviews."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reviews"
    label = "reviews"

    def ready(self) -> None:
        """Import signal handlers when Django starts the reviews app."""
        from apps.reviews import signals  # noqa: F401
