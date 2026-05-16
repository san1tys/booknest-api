from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    name = "apps.reviews"
    label = "reviews"

    def ready(self) -> None:
        from apps.reviews import signals  # noqa: F401
