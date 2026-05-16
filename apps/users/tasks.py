import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from django.conf import settings

from apps.abstract.async_io import AsyncOperationError, send_mail_async

logger = logging.getLogger(__name__)


@shared_task(name="apps.users.tasks.send_otp")
def send_otp(to_email: str, subject: str, message: str) -> bool:
    """Send an email through Django's configured email backend."""
    logger.info(
        "Queue worker sending OTP email to %s with subject '%s'", to_email, subject
    )
    try:
        sent_count = async_to_sync(send_mail_async)(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            timeout=settings.EMAIL_TIMEOUT,
            operation_name=f"otp_email:{to_email}",
        )
    except AsyncOperationError:
        logger.exception("Failed to send OTP email to %s", to_email)
        return False

    logger.info("OTP email send result for %s: %s", to_email, sent_count == 1)
    return sent_count == 1


send_OTP = send_otp
