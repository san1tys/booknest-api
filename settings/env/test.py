from settings.env.local import *  # noqa: F403

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
}

MIGRATION_MODULES = {
    "abstract": None,
    "bookings": None,
    "hotels": None,
    "reviews": None,
    "rooms": None,
    "users": None,
}
