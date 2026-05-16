from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.bookings.models import Booking, BookingStatus
from apps.hotels.models import Hotel
from apps.reviews.models import Review
from apps.rooms.models import Room
from apps.users.models import User

REVIEW_TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "reviews-endpoint-tests",
    }
}


def _bearer_token(user: User) -> str:
    """Mint an access token for the given user."""
    return str(RefreshToken.for_user(user).access_token)


@override_settings(
    CACHES=REVIEW_TEST_CACHES,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    LANGUAGE_CODE="en",
)
class ReviewEndpointTests(TestCase):
    """Endpoint tests for the hotel review viewset (list + create)."""

    def setUp(self) -> None:
        """Build guest with a confirmed past booking, plus owner without one."""
        cache.clear()
        self.guest = User.objects.create_user(
            email="guest@example.com",
            password="strongpass123",
            is_email_verified=True,
        )
        self.hotel_owner = User.objects.create_user(
            email="hotelowner@example.com",
            password="strongpass123",
            is_email_verified=True,
        )
        self.hotel = Hotel.objects.create(
            name="Reviewable Hotel", owner=self.hotel_owner
        )
        self.other_hotel = Hotel.objects.create(
            name="Unrelated Hotel", owner=self.hotel_owner
        )
        self.room = Room.objects.create(
            hotel=self.hotel,
            title="Room",
            price_per_night="120.00",
            capacity=2,
        )

        today = timezone.localdate()
        self.confirmed_booking = Booking.objects.create(
            user=self.guest,
            room=self.room,
            check_in=today - timedelta(days=7),
            check_out=today - timedelta(days=5),
            status=BookingStatus.CONFIRMED,
            total_price="240.00",
        )

        self.client = APIClient()
        self.guest_client = APIClient()
        self.guest_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {_bearer_token(self.guest)}"
        )
        self.owner_client = APIClient()
        self.owner_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {_bearer_token(self.hotel_owner)}"
        )

        self.list_url = f"/api/hotels/hotels/{self.hotel.pk}/reviews/"
        self.other_list_url = f"/api/hotels/hotels/{self.other_hotel.pk}/reviews/"

    # --- GET / ---------------------------------------------------------------

    def test_list_reviews_returns_200_for_anonymous(self) -> None:
        """Anyone can list reviews for a hotel."""
        Review.objects.create(
            user=self.guest, hotel=self.hotel, rating=5, text="Lovely stay"
        )
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["rating"], 5)

    def test_list_reviews_returns_empty_for_unrelated_hotel(self) -> None:
        """Hotels with no reviews return an empty list."""
        response = self.client.get(self.other_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.data), [])

    def test_list_reviews_put_not_allowed(self) -> None:
        """PUT is not allowed on the reviews endpoint."""
        response = self.client.put(self.list_url, {}, format="json")
        self.assertEqual(response.status_code, 405)

    # --- POST / --------------------------------------------------------------

    def test_create_review_returns_201_for_user_with_confirmed_booking(self) -> None:
        """A user with a confirmed booking can create a review."""
        response = self.guest_client.post(
            self.list_url, {"rating": 5, "text": "Great stay"}, format="json"
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(
            Review.objects.filter(user=self.guest, hotel=self.hotel).exists()
        )

    def test_create_review_returns_400_without_valid_booking(self) -> None:
        """A user with no confirmed/completed booking cannot review the hotel."""
        response = self.owner_client.post(
            self.list_url, {"rating": 5, "text": "I own this"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_create_review_returns_401_for_anonymous(self) -> None:
        """Anonymous users cannot create reviews."""
        response = self.client.post(
            self.list_url, {"rating": 4, "text": "Anon review"}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_create_review_returns_400_when_already_reviewed(self) -> None:
        """A user can only review a hotel once."""
        Review.objects.create(
            user=self.guest, hotel=self.hotel, rating=4, text="First review"
        )
        response = self.guest_client.post(
            self.list_url, {"rating": 5, "text": "Second review"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
