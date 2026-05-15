from settings.env.local import *  # noqa: F403


EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

MIGRATION_MODULES = {
    "abstract": None,
    "bookings": None,
    "hotels": None,
    "reviews": None,
    "rooms": None,
    "users": None,
}
