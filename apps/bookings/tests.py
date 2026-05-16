import asyncio
from datetime import timedelta
from unittest.mock import patch

from asgiref.sync import async_to_sync
from channels.testing.websocket import WebsocketCommunicator
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.abstract.async_io import AsyncOperationError
from apps.bookings.consumers import BookingStatusConsumer
from apps.bookings.models import Booking, BookingStatus
from apps.bookings.tasks import send_today_check_in_reminders
from apps.hotels.models import Hotel
from apps.rooms.models import Room
from apps.users.models import User

BOOKING_TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "bookings-endpoint-tests",
    }
}


def _bearer_token(user: User) -> str:
    """Mint an access token for the given user."""
    return str(RefreshToken.for_user(user).access_token)


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

    @patch("apps.bookings.tasks.send_mail_async")
    def test_send_today_check_in_reminders_handles_async_delivery_failure(
        self, mocked_send_mail_async
    ) -> None:
        """Reminder task continues and returns only successfully sent emails."""

        async def failing_send_mail_async(**kwargs) -> int:
            raise AsyncOperationError("smtp failure")

        mocked_send_mail_async.side_effect = failing_send_mail_async
        today = timezone.localdate()
        Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in=today,
            check_out=today + timedelta(days=1),
            status=BookingStatus.PENDING,
            total_price="150.00",
        )

        sent_count = send_today_check_in_reminders()

        self.assertEqual(sent_count, 0)


@override_settings(
    CACHES=BOOKING_TEST_CACHES,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    LANGUAGE_CODE="en",
)
class BookingEndpointTests(TestCase):
    """Endpoint tests for the booking viewset (list, create, availability, cancel)."""

    def setUp(self) -> None:
        """Build users, hotel, room, and one existing future booking."""
        cache.clear()
        self.guest = User.objects.create_user(
            email="guest@example.com",
            password="strongpass123",
            is_email_verified=True,
        )
        self.other_guest = User.objects.create_user(
            email="other@example.com",
            password="strongpass123",
            is_email_verified=True,
        )
        self.hotel_owner = User.objects.create_user(
            email="hotelowner@example.com",
            password="strongpass123",
            is_email_verified=True,
        )
        self.hotel = Hotel.objects.create(name="Stay Inn", owner=self.hotel_owner)
        self.room = Room.objects.create(
            hotel=self.hotel,
            title="Twin",
            price_per_night="100.00",
            capacity=2,
        )

        today = timezone.localdate()
        self.tomorrow = today + timedelta(days=1)
        self.day_after = today + timedelta(days=2)
        self.future_start = today + timedelta(days=10)
        self.future_end = today + timedelta(days=12)

        self.booking = Booking.objects.create(
            user=self.guest,
            room=self.room,
            check_in=self.future_start,
            check_out=self.future_end,
            status=BookingStatus.PENDING,
            total_price="200.00",
        )

        self.client = APIClient()
        self.guest_client = APIClient()
        self.guest_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {_bearer_token(self.guest)}"
        )
        self.other_client = APIClient()
        self.other_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {_bearer_token(self.other_guest)}"
        )
        self.owner_client = APIClient()
        self.owner_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {_bearer_token(self.hotel_owner)}"
        )

        self.list_url = "/api/bookings/v1/bookings/list"
        self.create_url = "/api/bookings/v1/bookings/create"
        self.availability_url = "/api/bookings/v1/bookings/availability"
        self.cancel_url = f"/api/bookings/v1/bookings/{self.booking.pk}/cancel"

    # --- GET /list -----------------------------------------------------------

    def test_list_bookings_returns_users_own_bookings_for_guest(self) -> None:
        """Guests see their own bookings."""
        response = self.guest_client.get(self.list_url)
        self.assertEqual(response.status_code, 200, response.data)
        ids = [b["id"] for b in response.data]
        self.assertIn(self.booking.pk, ids)

    def test_list_bookings_returns_hotel_bookings_for_hotel_owner(self) -> None:
        """Hotel owners see bookings on their hotels."""
        response = self.owner_client.get(self.list_url)
        self.assertEqual(response.status_code, 200, response.data)
        ids = [b["id"] for b in response.data]
        self.assertIn(self.booking.pk, ids)

    def test_list_bookings_returns_401_for_anonymous(self) -> None:
        """Anonymous request to booking list is rejected."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 401)

    # --- POST /create --------------------------------------------------------

    def test_create_booking_returns_201_for_free_dates(self) -> None:
        """Booking dates that do not overlap any existing booking succeed."""
        response = self.guest_client.post(
            self.create_url,
            {
                "room": self.room.pk,
                "check_in": self.tomorrow.isoformat(),
                "check_out": self.day_after.isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)

    def test_create_booking_returns_400_when_dates_overlap_existing(self) -> None:
        """Overlapping dates with an existing PENDING booking are rejected."""
        response = self.guest_client.post(
            self.create_url,
            {
                "room": self.room.pk,
                "check_in": self.future_start.isoformat(),
                "check_out": self.future_end.isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_booking_returns_400_when_checkout_not_after_checkin(self) -> None:
        """check_out must be strictly after check_in."""
        response = self.guest_client.post(
            self.create_url,
            {
                "room": self.room.pk,
                "check_in": self.tomorrow.isoformat(),
                "check_out": self.tomorrow.isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_booking_returns_401_for_anonymous(self) -> None:
        """Anonymous users cannot create bookings."""
        response = self.client.post(
            self.create_url,
            {
                "room": self.room.pk,
                "check_in": self.tomorrow.isoformat(),
                "check_out": self.day_after.isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    # --- GET /availability ---------------------------------------------------

    def test_availability_returns_true_for_free_dates(self) -> None:
        """Free dates return available=True."""
        response = self.guest_client.get(
            self.availability_url,
            {
                "room": self.room.pk,
                "check_in": self.tomorrow.isoformat(),
                "check_out": self.day_after.isoformat(),
            },
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["available"])

    def test_availability_returns_false_for_overlapping_dates(self) -> None:
        """Overlapping dates return available=False."""
        response = self.guest_client.get(
            self.availability_url,
            {
                "room": self.room.pk,
                "check_in": self.future_start.isoformat(),
                "check_out": self.future_end.isoformat(),
            },
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(response.data["available"])

    def test_availability_returns_400_for_invalid_dates(self) -> None:
        """check_out must be after check_in."""
        response = self.guest_client.get(
            self.availability_url,
            {
                "room": self.room.pk,
                "check_in": self.tomorrow.isoformat(),
                "check_out": self.tomorrow.isoformat(),
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_availability_returns_401_for_anonymous(self) -> None:
        """Anonymous users cannot check availability."""
        response = self.client.get(
            self.availability_url,
            {
                "room": self.room.pk,
                "check_in": self.tomorrow.isoformat(),
                "check_out": self.day_after.isoformat(),
            },
        )
        self.assertEqual(response.status_code, 401)

    # --- POST /{pk}/cancel ---------------------------------------------------

    def test_cancel_booking_returns_200_for_booking_owner(self) -> None:
        """The booking owner can cancel their booking."""
        response = self.guest_client.post(self.cancel_url)
        self.assertEqual(response.status_code, 200, response.data)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CANCELLED)

    def test_cancel_booking_returns_400_when_already_cancelled(self) -> None:
        """Cancelling an already-cancelled booking returns 400."""
        self.booking.status = BookingStatus.CANCELLED
        self.booking.save()
        response = self.guest_client.post(self.cancel_url)
        self.assertEqual(response.status_code, 400)

    def test_cancel_booking_returns_403_for_unrelated_user(self) -> None:
        """A user with no relation to the booking cannot cancel it."""
        response = self.other_client.post(self.cancel_url)
        self.assertEqual(response.status_code, 403)

    def test_cancel_booking_returns_404_for_missing_id(self) -> None:
        """Cancelling a non-existent booking yields 404."""
        response = self.guest_client.post("/api/bookings/v1/bookings/999999/cancel")
        self.assertEqual(response.status_code, 404)

    def test_cancel_booking_returns_401_for_anonymous(self) -> None:
        """Anonymous users cannot cancel bookings."""
        response = self.client.post(self.cancel_url)
        self.assertEqual(response.status_code, 401)


class BookingStatusConsumerTests(TransactionTestCase):
    """Tests for the BookingStatusConsumer websocket."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="ws-user@example.com",
            password="strongpass123",
            is_email_verified=True,
        )

    def _connect(self, token: str) -> WebsocketCommunicator:
        return WebsocketCommunicator(
            BookingStatusConsumer.as_asgi(),
            f"/ws/bookings/?token={token}",
        )

    def test_consumer_connects_and_receives_notify(self) -> None:
        """A valid JWT connects, and group_send via notify() reaches the socket."""
        token = str(AccessToken.for_user(self.user))

        async def scenario() -> None:
            communicator = self._connect(token)
            connected, _ = await communicator.connect()
            self.assertTrue(connected)

            sent = await BookingStatusConsumer.notify(
                user_id=self.user.id,
                booking_id=123,
                status=BookingStatus.CANCELLED,
            )
            self.assertTrue(sent)

            response = await communicator.receive_json_from()
            self.assertEqual(
                response,
                {
                    "type": "booking_status",
                    "booking_id": 123,
                    "status": BookingStatus.CANCELLED.value,
                },
            )

            await communicator.disconnect()

        async_to_sync(scenario)()

    @override_settings(ASYNC_IO_TIMEOUT_SECONDS=0.001)
    @patch("apps.bookings.consumers.get_channel_layer")
    def test_notify_returns_false_when_channel_send_times_out(
        self, mocked_get_channel_layer
    ) -> None:
        """Timed-out websocket notifications fail without raising to callers."""

        class SlowChannelLayer:
            async def group_send(self, group_name: str, message: dict) -> None:
                await asyncio.sleep(0.05)

        mocked_get_channel_layer.return_value = SlowChannelLayer()

        async def scenario() -> None:
            sent = await BookingStatusConsumer.notify(
                user_id=self.user.id,
                booking_id=123,
                status=BookingStatus.CANCELLED,
            )

            self.assertFalse(sent)

        async_to_sync(scenario)()

    def test_consumer_rejects_missing_token(self) -> None:
        """Connecting without a token closes the handshake."""

        async def scenario() -> None:
            communicator = WebsocketCommunicator(
                BookingStatusConsumer.as_asgi(),
                "/ws/bookings/",
            )
            connected, _ = await communicator.connect()
            self.assertFalse(connected)
            await communicator.disconnect()

        async_to_sync(scenario)()
