from apps.users.models import User


def validate_is_admin(user: User) -> bool:
    """Validate if the user has admin privileges."""
    return user.is_staff


def validate_is_active(user: User) -> bool:
    """Validate if the user account is active."""
    return user.is_active
