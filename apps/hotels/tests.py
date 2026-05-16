from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.hotels.models import Hotel
from apps.users.models import User

HOTEL_TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "hotels-endpoint-tests",
    }
}


def _bearer_token(user: User) -> str:
    """Mint an access token for the given user."""
    return str(RefreshToken.for_user(user).access_token)


@override_settings(
    CACHES=HOTEL_TEST_CACHES,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    LANGUAGE_CODE="en",
)
class HotelEndpointTests(TestCase):
    """Endpoint tests for the hotel viewset."""

    def setUp(self) -> None:
        """Build owner/intruder users plus a seeded hotel."""
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
        self.hotel = Hotel.objects.create(
            name="Owner Hotel",
            owner=self.owner,
            rating=4,
            city="Astana",
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

        self.list_url = "/api/hotels/v1/hotels/list"
        self.create_url = "/api/hotels/v1/hotels/create"
        self.detail_url = f"/api/hotels/v1/hotels/{self.hotel.pk}/details"
        self.update_url = f"/api/hotels/v1/hotels/{self.hotel.pk}/update"
        self.delete_url = f"/api/hotels/v1/hotels/{self.hotel.pk}/delete"

    # --- GET /list -----------------------------------------------------------

    def test_list_hotels_returns_200_for_anonymous(self) -> None:
        """Anyone can list hotels and the seeded hotel appears."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        names = [hotel["name"] for hotel in response.data]
        self.assertIn(self.hotel.name, names)

    def test_list_hotels_empty_when_none_exist(self) -> None:
        """Listing returns an empty array when no hotels are present."""
        Hotel.objects.all().delete()
        cache.clear()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.data), [])

    def test_list_hotels_post_not_allowed(self) -> None:
        """POST to the list URL is not allowed."""
        response = self.client.post(self.list_url, {}, format="json")
        self.assertEqual(response.status_code, 405)

    # --- GET /{id}/details ---------------------------------------------------

    def test_hotel_details_returns_200(self) -> None:
        """Detail endpoint returns the hotel payload."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], self.hotel.name)

    def test_hotel_details_returns_404_for_missing(self) -> None:
        """Unknown hotel id yields a 404."""
        response = self.client.get("/api/hotels/v1/hotels/999999/details")
        self.assertEqual(response.status_code, 404)

    def test_hotel_details_post_not_allowed(self) -> None:
        """POST to the detail URL is not allowed."""
        response = self.client.post(self.detail_url, {}, format="json")
        self.assertEqual(response.status_code, 405)

    # --- POST /create --------------------------------------------------------

    def test_create_hotel_returns_201_for_authenticated(self) -> None:
        """Authenticated user can create a hotel and it appears in the next list."""
        response = self.owner_client.post(
            self.create_url,
            {"name": "Brand New Hotel", "rating": 5, "city": "Almaty"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["name"], "Brand New Hotel")
        cache.clear()
        list_response = self.client.get(self.list_url)
        names = [hotel["name"] for hotel in list_response.data]
        self.assertIn("Brand New Hotel", names)

    def test_create_hotel_returns_401_for_anonymous(self) -> None:
        """Anonymous users cannot create hotels."""
        response = self.client.post(
            self.create_url, {"name": "Anon Hotel"}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_create_hotel_returns_400_for_duplicate_name(self) -> None:
        """Hotel names must be unique."""
        response = self.owner_client.post(
            self.create_url, {"name": self.hotel.name}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    # --- PUT /{id}/update ----------------------------------------------------

    def test_update_hotel_returns_200_for_owner(self) -> None:
        """Owner can update their hotel."""
        response = self.owner_client.put(
            self.update_url,
            {"name": "Renamed Hotel", "rating": 3},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.hotel.refresh_from_db()
        self.assertEqual(self.hotel.name, "Renamed Hotel")

    def test_update_hotel_returns_403_for_non_owner(self) -> None:
        """A different authenticated user cannot update someone else's hotel."""
        response = self.intruder_client.put(
            self.update_url, {"name": "Hijacked"}, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_update_hotel_returns_401_for_anonymous(self) -> None:
        """Anonymous users cannot update hotels."""
        response = self.client.put(
            self.update_url, {"name": "Anon Rename"}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    # --- DELETE /{id}/delete -------------------------------------------------

    def test_delete_hotel_returns_204_for_owner(self) -> None:
        """Owner can delete their hotel and the next list omits it."""
        response = self.owner_client.delete(self.delete_url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Hotel.objects.filter(pk=self.hotel.pk).exists())
        cache.clear()
        list_response = self.client.get(self.list_url)
        names = [hotel["name"] for hotel in list_response.data]
        self.assertNotIn(self.hotel.name, names)

    def test_delete_hotel_returns_403_for_non_owner(self) -> None:
        """A non-owner cannot delete the hotel."""
        response = self.intruder_client.delete(self.delete_url)
        self.assertEqual(response.status_code, 403)

    def test_delete_hotel_returns_401_for_anonymous(self) -> None:
        """Anonymous users cannot delete hotels."""
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, 401)
