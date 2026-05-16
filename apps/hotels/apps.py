from django.apps import AppConfig


class HotelsConfig(AppConfig):
    name = "apps.hotels"
    label = "hotels"

    def ready(self) -> None:
        from apps.hotels import signals  # noqa: F401
