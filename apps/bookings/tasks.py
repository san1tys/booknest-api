import logging
from collections import defaultdict
from datetime import date

from asgiref.sync import async_to_sync
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.abstract.async_io import AsyncOperationError, send_mail_async
from apps.bookings.models import Booking, BookingStatus
from apps.users.models import User

logger = logging.getLogger(__name__)


def build_check_in_reminder_message(user: User, bookings: list[Booking]) -> str:
    """Build a reminder email body for today's check-ins."""
    greeting_name = user.first_name or user.email
    lines = [
        f"Hi {greeting_name},",
        "",
        "This is your BookNest reminder for today's check-in:",
        "",
    ]

    for booking in bookings:
        lines.append(
            f"- {booking.room.hotel.name}: {booking.room.title} "
            f"from {booking.check_in} to {booking.check_out}"
        )

    lines.extend(
        [
            "",
            "We hope you have a great stay.",
        ]
    )
    return "\n".join(lines)


@shared_task(name="apps.bookings.tasks.send_today_check_in_reminders")
def send_today_check_in_reminders(target_date_iso: str | None = None) -> int:
    """Send one reminder email per user for bookings that start today."""
    reminder_date = (
        date.fromisoformat(target_date_iso) if target_date_iso else timezone.localdate()
    )

    bookings = (
        Booking.objects.select_related("user", "room", "room__hotel")
        .filter(
            check_in=reminder_date,
            status__in=(BookingStatus.PENDING, BookingStatus.CONFIRMED),
            user__is_active=True,
        )
        .order_by("user_id", "check_in", "check_out", "id")
    )

    bookings_by_user: dict[int, list[Booking]] = defaultdict(list)
    for booking in bookings:
        bookings_by_user[booking.user_id].append(booking)

    reminders_sent = 0
    for user_bookings in bookings_by_user.values():
        user = user_bookings[0].user
        logger.info(
            "Sending check-in reminder to %s for %s booking(s) on %s",
            user.email,
            len(user_bookings),
            reminder_date,
        )
        try:
            sent_count = async_to_sync(send_mail_async)(
                subject="BookNest check-in reminder",
                message=build_check_in_reminder_message(user, user_bookings),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                timeout=settings.EMAIL_TIMEOUT,
                operation_name=f"check_in_reminder:{user.email}",
            )
        except AsyncOperationError:
            logger.exception("Failed to send check-in reminder to %s", user.email)
            continue

        if sent_count == 1:
            reminders_sent += 1

    logger.info(
        "Finished sending today's check-in reminders for %s. Emails sent: %s",
        reminder_date,
        reminders_sent,
    )
    return reminders_sent
