from django.apps import AppConfig


class HotelsConfig(AppConfig):
    """App configuration for hotels."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.hotels"
    label = "hotels"

    def ready(self) -> None:
        """Import signal handlers when Django starts the hotels app."""
        from apps.hotels import signals  # noqa: F401
