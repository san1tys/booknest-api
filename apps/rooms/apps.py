from django.apps import AppConfig


class RoomsConfig(AppConfig):
    """App configuration for rooms."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.rooms"
    label = "rooms"
