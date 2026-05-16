import logging
import secrets
import string

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager

from apps.abstract.redis_storage import (
    delete_temporary_data,
    get_temporary_data,
    set_temporary_data,
)
from apps.users.models import User
from apps.users.tasks import send_OTP as send_email

logger = logging.getLogger(__name__)

EMAIL_VERIFICATION_OTP_KEY = "email_verification_otp"


def normalize_email_identifier(email: str) -> str:
    """Return a stable email key for OTP cache storage."""
    return BaseUserManager.normalize_email(email).lower()


def generate_email_verification_otp() -> str:
    """Generate a numeric OTP for email verification."""
    digits = string.digits
    return "".join(
        secrets.choice(digits) for _ in range(settings.EMAIL_VERIFICATION_OTP_LENGTH)
    )


def set_email_verification_otp(email: str, otp: str) -> bool:
    """Store a verification OTP in temporary storage."""
    return set_temporary_data(
        EMAIL_VERIFICATION_OTP_KEY,
        normalize_email_identifier(email),
        otp,
        timeout=settings.EMAIL_VERIFICATION_OTP_TTL_SECONDS,
    )


def get_email_verification_otp(email: str) -> str | None:
    """Read a stored verification OTP."""
    return get_temporary_data(
        EMAIL_VERIFICATION_OTP_KEY,
        normalize_email_identifier(email),
    )


def delete_email_verification_otp(email: str) -> bool:
    """Delete a stored verification OTP."""
    return delete_temporary_data(
        EMAIL_VERIFICATION_OTP_KEY,
        normalize_email_identifier(email),
    )


def build_email_verification_message(user: User, otp: str) -> str:
    """Build the email body for a verification OTP."""
    greeting_name = user.first_name or user.email
    return (
        f"Hi {greeting_name},\n\n"
        f"Your BookNest verification code is: {otp}\n\n"
        f"This code expires in {settings.EMAIL_VERIFICATION_OTP_TTL_SECONDS // 60} minutes."
    )


def dispatch_email_verification_otp(user: User) -> str:
    """Generate, store, and enqueue an email verification OTP."""
    otp = generate_email_verification_otp()
    set_email_verification_otp(user.email, otp)
    logger.info("Queueing email verification OTP for %s: %s", user.email, otp)
    send_email.delay(
        to_email=user.email,
        subject="Verify your BookNest email",
        message=build_email_verification_message(user, otp),
    )
    return otp
