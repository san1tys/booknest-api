from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.bookings.models import Booking, BookingStatus
from apps.bookings.tasks import send_today_check_in_reminders
from apps.hotels.models import Hotel
from apps.rooms.models import Room
from apps.users.models import User


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class BookingReminderTaskTests(TestCase):
    """Tests for today's booking reminder email task."""

    def setUp(self) -> None:
        """Create shared booking fixtures."""
        self.user = User.objects.create_user(
            email="guest@example.com",
            password="strongpass123",
            first_name="Guest",
            is_email_verified=True,
        )
        self.other_user = User.objects.create_user(
            email="cancelled@example.com",
            password="strongpass123",
            first_name="Cancelled",
            is_email_verified=True,
        )
        self.hotel = Hotel.objects.create(name="Sunrise Hotel")
        self.room = Room.objects.create(
            hotel=self.hotel,
            title="Deluxe Room",
            price_per_night="150.00",
            capacity=2,
            quantity=4,
        )
        self.other_room = Room.objects.create(
            hotel=self.hotel,
            title="Suite",
            price_per_night="220.00",
            capacity=3,
            quantity=2,
        )

    def test_send_today_check_in_reminders_emails_each_user_once(self) -> None:
        """Users with one or more bookings starting today get a single reminder email."""
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)

        Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in=today,
            check_out=tomorrow,
            status=BookingStatus.PENDING,
            total_price="150.00",
        )
        Booking.objects.create(
            user=self.user,
            room=self.other_room,
            check_in=today,
            check_out=tomorrow,
            status=BookingStatus.CONFIRMED,
            total_price="220.00",
        )
        Booking.objects.create(
            user=self.other_user,
            room=self.room,
            check_in=today,
            check_out=tomorrow,
            status=BookingStatus.CANCELLED,
            total_price="150.00",
        )

        sent_count = send_today_check_in_reminders()

        self.assertEqual(sent_count, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["guest@example.com"])
        self.assertIn("Deluxe Room", mail.outbox[0].body)
        self.assertIn("Suite", mail.outbox[0].body)

    def test_send_today_check_in_reminders_skips_other_dates(self) -> None:
        """Bookings not starting today do not trigger reminder emails."""
        tomorrow = timezone.localdate() + timedelta(days=1)

        Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in=tomorrow,
            check_out=tomorrow + timedelta(days=1),
            status=BookingStatus.CONFIRMED,
            total_price="150.00",
        )

        sent_count = send_today_check_in_reminders()

        self.assertEqual(sent_count, 0)
        self.assertEqual(len(mail.outbox), 0)
