import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


logger = logging.getLogger(__name__)


@shared_task
def send_OTP(to_email: str, subject: str, message: str) -> bool:
    """Send an email through Django's configured email backend."""
    logger.info("Sending OTP email to %s with subject '%s'", to_email, subject)
    sent_count = send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )
    logger.info("OTP email send result for %s: %s", to_email, sent_count == 1)
    return sent_count == 1

