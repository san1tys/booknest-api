from django.apps import AppConfig


class AbstractConfig(AppConfig):
    """App configuration for shared abstract utilities."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.abstract"
    label = "abstract"
