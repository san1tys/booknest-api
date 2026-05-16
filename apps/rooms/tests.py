from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.hotels.models import Hotel
from apps.rooms.models import Room
from apps.users.models import User


ROOM_TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "rooms-endpoint-tests",
    }
}


def _bearer_token(user: User) -> str:
    """Mint an access token for the given user."""
    return str(RefreshToken.for_user(user).access_token)


@override_settings(
    CACHES=ROOM_TEST_CACHES,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    LANGUAGE_CODE="en",
)
class RoomEndpointTests(TestCase):
    """Endpoint tests for the room viewset."""

    def setUp(self) -> None:
        """Build owner/intruder users and two hotels with one shared room."""
        cache.clear()
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="strongpass123",
            is_email_verified=True,
        )
        self.intruder = User.objects.create_user(
            email="intruder@example.com",
            password="strongpass123",
            is_email_verified=True,
        )
        self.hotel = Hotel.objects.create(name="Owner Hotel", owner=self.owner)
        self.other_hotel = Hotel.objects.create(
            name="Intruder Hotel", owner=self.intruder
        )
        self.room = Room.objects.create(
            hotel=self.hotel,
            title="Standard",
            price_per_night="100.00",
            capacity=2,
            quantity=1,
        )

        self.client = APIClient()
        self.owner_client = APIClient()
        self.owner_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {_bearer_token(self.owner)}"
        )
        self.intruder_client = APIClient()
        self.intruder_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {_bearer_token(self.intruder)}"
        )

        self.list_url = "/api/hotels/v1/rooms/list"
        self.create_url = "/api/hotels/v1/rooms/create"
        self.detail_url = f"/api/hotels/v1/rooms/{self.room.pk}/details"
        self.update_url = f"/api/hotels/v1/rooms/{self.room.pk}/update"
        self.delete_url = f"/api/hotels/v1/rooms/{self.room.pk}/delete"

    # --- GET /list -----------------------------------------------------------

    def test_list_rooms_returns_200_for_anonymous(self) -> None:
        """Anyone can list rooms."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        titles = [room["title"] for room in response.data]
        self.assertIn(self.room.title, titles)

    def test_list_rooms_filters_by_hotel_query_param(self) -> None:
        """Filtering by hotel excludes rooms of other hotels."""
        response = self.client.get(
            self.list_url, {"hotel": self.other_hotel.pk}
        )
        self.assertEqual(response.status_code, 200)
        for room in response.data:
            self.assertEqual(room["hotel"], self.other_hotel.pk)

    def test_list_rooms_post_not_allowed(self) -> None:
        """POST to the list URL is not allowed."""
        response = self.client.post(self.list_url, {}, format="json")
        self.assertEqual(response.status_code, 405)

    # --- GET /{id}/details ---------------------------------------------------

    def test_room_details_returns_200(self) -> None:
        """Detail endpoint returns the room payload."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], self.room.title)

    def test_room_details_returns_404_for_missing(self) -> None:
        """Unknown room id yields 404."""
        response = self.client.get("/api/hotels/v1/rooms/999999/details")
        self.assertEqual(response.status_code, 404)

    def test_room_details_post_not_allowed(self) -> None:
        """POST to the detail URL is not allowed."""
        response = self.client.post(self.detail_url, {}, format="json")
        self.assertEqual(response.status_code, 405)

    # --- POST /create --------------------------------------------------------

    def test_create_room_returns_201_for_hotel_owner(self) -> None:
        """Hotel owner can create a room in their hotel."""
        response = self.owner_client.post(
            self.create_url,
            {
                "hotel": self.hotel.pk,
                "title": "Suite",
                "price_per_night": "200.00",
                "capacity": 3,
                "quantity": 2,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        cache.clear()
        list_response = self.client.get(self.list_url)
        titles = [room["title"] for room in list_response.data]
        self.assertIn("Suite", titles)

    def test_create_room_returns_403_when_not_hotel_owner(self) -> None:
        """An authenticated non-owner cannot create rooms in another's hotel."""
        response = self.intruder_client.post(
            self.create_url,
            {
                "hotel": self.hotel.pk,
                "title": "Sneaky Room",
                "price_per_night": "100.00",
                "capacity": 2,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_create_room_returns_401_for_anonymous(self) -> None:
        """Anonymous users cannot create rooms."""
        response = self.client.post(
            self.create_url,
            {
                "hotel": self.hotel.pk,
                "title": "Anon Room",
                "price_per_night": "100.00",
                "capacity": 2,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    # --- PUT /{id}/update ----------------------------------------------------

    def test_update_room_returns_200_for_hotel_owner(self) -> None:
        """Hotel owner can update their room."""
        response = self.owner_client.put(
            self.update_url,
            {
                "hotel": self.hotel.pk,
                "title": "Renamed Room",
                "price_per_night": "120.00",
                "capacity": 2,
                "quantity": 1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.room.refresh_from_db()
        self.assertEqual(self.room.title, "Renamed Room")

    def test_update_room_returns_403_for_non_owner(self) -> None:
        """A non-owner cannot update someone else's room."""
        response = self.intruder_client.put(
            self.update_url,
            {
                "hotel": self.hotel.pk,
                "title": "Hijacked",
                "price_per_night": "100.00",
                "capacity": 2,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_update_room_rejects_anonymous(self) -> None:
        """Anonymous users cannot update rooms (rejected by the view's owner check)."""
        response = self.client.put(
            self.update_url,
            {
                "hotel": self.hotel.pk,
                "title": "Anon Update",
                "price_per_night": "100.00",
                "capacity": 2,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    # --- DELETE /{id}/delete -------------------------------------------------

    def test_delete_room_returns_204_for_hotel_owner(self) -> None:
        """Hotel owner can delete their own room."""
        response = self.owner_client.delete(self.delete_url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Room.objects.filter(pk=self.room.pk).exists())

    def test_delete_room_returns_403_for_non_owner(self) -> None:
        """A non-owner cannot delete a room."""
        response = self.intruder_client.delete(self.delete_url)
        self.assertEqual(response.status_code, 403)

    def test_delete_room_rejects_anonymous(self) -> None:
        """Anonymous users cannot delete rooms (rejected by the view's owner check)."""
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, 403)
