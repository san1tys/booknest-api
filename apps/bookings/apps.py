from django.apps import AppConfig


class BookingsConfig(AppConfig):
    """App configuration for bookings."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.bookings"
    label = "bookings"
