"""Shared testing helpers used across Django and pytest test modules."""

from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User


def bearer_token(user: User) -> str:
    """Return a JWT access token string for the given user."""
    return str(RefreshToken.for_user(user).access_token)


def build_locmem_caches(location: str) -> dict[str, dict[str, str]]:
    """Build a locmem cache config with a predictable isolated location."""
    return {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": location,
        }
    }
