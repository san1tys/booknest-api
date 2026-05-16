from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

import pytest
from django.core.cache import cache
from django.utils import timezone
from rest_framework.response import Response as DRFResponse
from rest_framework.test import APIClient

from apps.abstract.testing import bearer_token
from apps.bookings.models import Booking, BookingStatus
from apps.hotels.models import Hotel
from apps.reviews.models import Review
from apps.rooms.models import Room
from apps.users.models import User
from apps.users.services import set_email_verification_otp


@dataclass(slots=True)
class EndpointCase:
    """Describe one request/response scenario for an endpoint matrix test."""

    client_name: str
    method: str
    url: str
    expected_status: int
    data: dict[str, Any] | None = None
    format: str | None = None
    expected_keys: tuple[str, ...] = ()
    absent_keys: tuple[str, ...] = ()
    setup: Callable[[], None] | None = None
    post_assert: Callable[[DRFResponse], None] | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def _build_client(user: User | None = None) -> APIClient:
    """Create an API client, optionally authenticated as the given user."""
    client = APIClient()
    if user is not None:
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {bearer_token(user)}")
    return client


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    """Keep the cache isolated across pytest endpoint scenarios."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_state(db: None, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Build shared users, models, clients, and URLs for endpoint scenarios."""
    email_delay_calls: list[dict[str, Any]] = []

    from apps.users import services

    def fake_delay(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
        """Record outbound OTP email calls without invoking Celery."""
        email_delay_calls.append({"args": args, "kwargs": kwargs})

    monkeypatch.setattr(services.send_email, "delay", fake_delay)

    password = "strongpass123"

    verified_user = User.objects.create_user(
        email="verified@example.com",
        password=password,
        first_name="Verified",
        is_email_verified=True,
    )
    unverified_user = User.objects.create_user(
        email="unverified@example.com",
        password=password,
        first_name="Unverified",
    )
    owner = User.objects.create_user(
        email="owner@example.com",
        password=password,
        is_email_verified=True,
    )
    intruder = User.objects.create_user(
        email="intruder@example.com",
        password=password,
        is_email_verified=True,
    )
    hotel_owner = User.objects.create_user(
        email="hotelowner@example.com",
        password=password,
        is_email_verified=True,
    )
    guest = User.objects.create_user(
        email="guest@example.com",
        password=password,
        is_email_verified=True,
    )
    other_guest = User.objects.create_user(
        email="other@example.com",
        password=password,
        is_email_verified=True,
    )
    reviewer = User.objects.create_user(
        email="reviewer@example.com",
        password=password,
        is_email_verified=True,
    )

    owner_hotel = Hotel.objects.create(
        name="Owner Hotel",
        owner=owner,
        rating=4,
        city="Astana",
    )
    other_hotel = Hotel.objects.create(
        name="Intruder Hotel",
        owner=intruder,
        city="Almaty",
    )
    review_hotel = Hotel.objects.create(
        name="Reviewable Hotel",
        owner=hotel_owner,
        city="Shymkent",
    )

    owner_room = Room.objects.create(
        hotel=owner_hotel,
        title="Standard",
        price_per_night="100.00",
        capacity=2,
        quantity=1,
    )
    review_room = Room.objects.create(
        hotel=review_hotel,
        title="Twin",
        price_per_night="120.00",
        capacity=2,
        quantity=1,
    )

    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    future_start = today + timedelta(days=10)
    future_end = today + timedelta(days=12)

    pending_booking = Booking.objects.create(
        user=guest,
        room=review_room,
        check_in=future_start,
        check_out=future_end,
        status=BookingStatus.PENDING,
        total_price="240.00",
    )
    Booking.objects.create(
        user=guest,
        room=review_room,
        check_in=today - timedelta(days=7),
        check_out=today - timedelta(days=5),
        status=BookingStatus.CONFIRMED,
        total_price="240.00",
    )
    Booking.objects.create(
        user=reviewer,
        room=review_room,
        check_in=today - timedelta(days=10),
        check_out=today - timedelta(days=8),
        status=BookingStatus.COMPLETED,
        total_price="240.00",
    )
    existing_review = Review.objects.create(
        user=reviewer,
        hotel=review_hotel,
        rating=4,
        text="Nice stay",
    )

    clients = {
        "anonymous": _build_client(),
        "verified": _build_client(verified_user),
        "unverified": _build_client(unverified_user),
        "owner": _build_client(owner),
        "intruder": _build_client(intruder),
        "hotel_owner": _build_client(hotel_owner),
        "guest": _build_client(guest),
        "other_guest": _build_client(other_guest),
        "reviewer": _build_client(reviewer),
    }

    urls = {
        "users_me": "/api/users/v1/users/me",
        "users_register": "/api/users/v1/users/register",
        "users_verify_email": "/api/users/v1/users/verify-email",
        "users_resend_verification": "/api/users/v1/users/resend-verification",
        "users_login": "/api/users/v1/users/login",
        "users_logout": "/api/users/v1/users/logout",
        "users_language": "/api/users/v1/users/language",
        "hotels_list": "/api/hotels/v1/hotels/list",
        "hotels_create": "/api/hotels/v1/hotels/create",
        "hotels_detail": f"/api/hotels/v1/hotels/{owner_hotel.pk}/details",
        "hotels_update": f"/api/hotels/v1/hotels/{owner_hotel.pk}/update",
        "hotels_delete": f"/api/hotels/v1/hotels/{owner_hotel.pk}/delete",
        "rooms_list": "/api/hotels/v1/rooms/list",
        "rooms_create": "/api/hotels/v1/rooms/create",
        "rooms_detail": f"/api/hotels/v1/rooms/{owner_room.pk}/details",
        "rooms_update": f"/api/hotels/v1/rooms/{owner_room.pk}/update",
        "rooms_delete": f"/api/hotels/v1/rooms/{owner_room.pk}/delete",
        "reviews_list": f"/api/hotels/hotels/{review_hotel.pk}/reviews/",
        "reviews_create": f"/api/hotels/hotels/{review_hotel.pk}/reviews/",
        "bookings_list": "/api/bookings/v1/bookings/list",
        "bookings_create": "/api/bookings/v1/bookings/create",
        "bookings_availability": "/api/bookings/v1/bookings/availability",
        "bookings_cancel": f"/api/bookings/v1/bookings/{pending_booking.pk}/cancel",
    }

    return {
        "password": password,
        "users": {
            "verified": verified_user,
            "unverified": unverified_user,
            "owner": owner,
            "intruder": intruder,
            "hotel_owner": hotel_owner,
            "guest": guest,
            "other_guest": other_guest,
            "reviewer": reviewer,
        },
        "hotels": {
            "owner": owner_hotel,
            "other": other_hotel,
            "review": review_hotel,
        },
        "rooms": {
            "owner": owner_room,
            "review": review_room,
        },
        "bookings": {
            "pending": pending_booking,
        },
        "reviews": {
            "existing": existing_review,
        },
        "clients": clients,
        "urls": urls,
        "email_delay_calls": email_delay_calls,
        "dates": {
            "today": today,
            "tomorrow": tomorrow,
            "day_after": day_after,
            "future_start": future_start,
            "future_end": future_end,
        },
    }


@pytest.fixture
def endpoint_case_map(api_state: dict[str, Any]) -> dict[str, dict[str, EndpointCase]]:
    """Build one success case and two failure cases for each API endpoint."""
    users = api_state["users"]
    hotels = api_state["hotels"]
    rooms = api_state["rooms"]
    bookings = api_state["bookings"]
    urls = api_state["urls"]
    dates = api_state["dates"]

    def seed_valid_otp() -> None:
        """Store a valid OTP for the unverified shared user."""
        set_email_verification_otp(users["unverified"].email, "654321")

    def prepare_logout_refresh_token() -> None:
        """Create a refresh token payload for the logout success case."""
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(users["verified"])
        api_state["logout_refresh"] = str(refresh)

    def assert_me(response: DRFResponse) -> None:
        """Verify the `/me` response exposes the authenticated user only."""
        assert response.data["email"] == users["verified"].email
        assert "password" not in response.data

    def assert_register(response: DRFResponse) -> None:
        """Verify registration created a user and queued an OTP email."""
        assert User.objects.filter(email="newcomer@example.com").exists()
        assert len(api_state["email_delay_calls"]) == 1
        assert "user" in response.data

    def assert_verify_email(response: DRFResponse) -> None:
        """Verify a successful OTP confirmation flips the user state."""
        users["unverified"].refresh_from_db()
        assert users["unverified"].is_email_verified is True
        assert response.data["detail"]

    def assert_resend(response: DRFResponse) -> None:
        """Verify resend verification enqueues one email task call."""
        assert len(api_state["email_delay_calls"]) == 1
        assert response.data["detail"]

    def assert_login(response: DRFResponse) -> None:
        """Verify login returns both access and refresh credentials."""
        assert response.data["email"] == users["verified"].email
        assert "access" in response.data
        assert "refresh" in response.data

    def assert_logout(response: DRFResponse) -> None:
        """Verify logout blacklists the prepared refresh token."""
        refresh_response = api_state["clients"]["anonymous"].post(
            "/api/auth/token/refresh/",
            {"refresh": api_state["logout_refresh"]},
            format="json",
        )
        assert refresh_response.status_code == 401
        assert response.data["detail"]

    def assert_language(response: DRFResponse) -> None:
        """Verify language preference responses echo the accepted value."""
        assert response.data["language"] == "en"

    def assert_hotel_created(response: DRFResponse) -> None:
        """Verify hotel creation persists the requested hotel."""
        assert Hotel.objects.filter(name="Brand New Hotel").exists()
        assert response.data["name"] == "Brand New Hotel"

    def assert_hotel_updated(response: DRFResponse) -> None:
        """Verify hotel update persists the renamed hotel."""
        hotels["owner"].refresh_from_db()
        assert hotels["owner"].name == "Renamed Hotel"
        assert response.data["name"] == "Renamed Hotel"

    def assert_hotel_detail(response: DRFResponse) -> None:
        """Verify hotel detail returns the seeded hotel payload."""
        assert response.data["name"] == hotels["owner"].name

    def assert_hotel_list(response: DRFResponse) -> None:
        """Verify hotel list contains the seeded hotel entry."""
        names = [hotel["name"] for hotel in response.data["results"]]
        assert hotels["owner"].name in names

    def assert_hotel_deleted(response: DRFResponse) -> None:
        """Verify hotel deletion removes the record from persistence."""
        assert not Hotel.objects.filter(pk=hotels["owner"].pk).exists()
        assert response.status_code == 204

    def assert_room_created(response: DRFResponse) -> None:
        """Verify room creation persists the requested room."""
        assert Room.objects.filter(title="Suite").exists()
        assert response.data["title"] == "Suite"

    def assert_room_updated(response: DRFResponse) -> None:
        """Verify room update persists the renamed room."""
        rooms["owner"].refresh_from_db()
        assert rooms["owner"].title == "Renamed Room"
        assert response.data["title"] == "Renamed Room"

    def assert_room_detail(response: DRFResponse) -> None:
        """Verify room detail returns the seeded room payload."""
        assert response.data["title"] == rooms["owner"].title

    def assert_room_list(response: DRFResponse) -> None:
        """Verify room list contains the seeded room entry."""
        titles = [room["title"] for room in response.data["results"]]
        assert rooms["owner"].title in titles

    def assert_room_deleted(response: DRFResponse) -> None:
        """Verify room deletion removes the record from persistence."""
        assert not Room.objects.filter(pk=rooms["owner"].pk).exists()
        assert response.status_code == 204

    def assert_review_list(response: DRFResponse) -> None:
        """Verify hotel review list returns seeded review data."""
        assert response.data["count"] >= 1
        assert response.data["results"][0]["hotel"] == hotels["review"].pk

    def assert_review_created(response: DRFResponse) -> None:
        """Verify review creation persists the guest review."""
        assert Review.objects.filter(
            user=users["guest"], hotel=hotels["review"]
        ).exists()
        assert response.data["rating"] == 5

    def assert_booking_created(response: DRFResponse) -> None:
        """Verify booking creation persists the expected booking row."""
        assert Booking.objects.filter(
            user=users["guest"],
            room=rooms["review"],
            check_in=dates["tomorrow"],
            check_out=dates["day_after"],
        ).exists()
        assert response.data["room"] == rooms["review"].pk

    def assert_booking_list(response: DRFResponse) -> None:
        """Verify booking list includes the seeded pending booking."""
        ids = [booking["id"] for booking in response.data["results"]]
        assert bookings["pending"].pk in ids

    def assert_booking_availability(response: DRFResponse) -> None:
        """Verify availability response marks the free slot as available."""
        assert response.data["available"] is True
        assert response.data["room"] == rooms["review"].pk

    def assert_booking_cancel(response: DRFResponse) -> None:
        """Verify booking cancellation persists the cancelled status."""
        bookings["pending"].refresh_from_db()
        assert bookings["pending"].status == BookingStatus.CANCELLED
        assert response.data["status"] == BookingStatus.CANCELLED

    return {
        "users_me": {
            "good": EndpointCase(
                "verified",
                "get",
                urls["users_me"],
                200,
                expected_keys=("email", "is_email_verified"),
                absent_keys=("password",),
                post_assert=assert_me,
            ),
            "bad_1": EndpointCase("anonymous", "get", urls["users_me"], 401),
            "bad_2": EndpointCase(
                "verified",
                "post",
                urls["users_me"],
                405,
                data={},
                format="json",
            ),
        },
        "users_register": {
            "good": EndpointCase(
                "anonymous",
                "post",
                urls["users_register"],
                201,
                data={
                    "email": "newcomer@example.com",
                    "password": api_state["password"],
                    "first_name": "New",
                    "last_name": "Comer",
                },
                format="json",
                expected_keys=("detail", "user"),
                post_assert=assert_register,
            ),
            "bad_1": EndpointCase(
                "anonymous",
                "post",
                urls["users_register"],
                400,
                data={"password": api_state["password"], "first_name": "NoEmail"},
                format="json",
            ),
            "bad_2": EndpointCase(
                "verified",
                "post",
                urls["users_register"],
                401,
                data={
                    "email": "auth-user@example.com",
                    "password": api_state["password"],
                },
                format="json",
            ),
        },
        "users_verify_email": {
            "good": EndpointCase(
                "anonymous",
                "post",
                urls["users_verify_email"],
                200,
                data={"email": users["unverified"].email, "otp": "654321"},
                format="json",
                expected_keys=("detail",),
                setup=seed_valid_otp,
                post_assert=assert_verify_email,
            ),
            "bad_1": EndpointCase(
                "anonymous",
                "post",
                urls["users_verify_email"],
                400,
                data={"email": users["unverified"].email, "otp": "999999"},
                format="json",
                setup=seed_valid_otp,
            ),
            "bad_2": EndpointCase(
                "anonymous",
                "post",
                urls["users_verify_email"],
                404,
                data={"email": "missing@example.com", "otp": "123456"},
                format="json",
            ),
        },
        "users_resend_verification": {
            "good": EndpointCase(
                "anonymous",
                "post",
                urls["users_resend_verification"],
                200,
                data={"email": users["unverified"].email},
                format="json",
                expected_keys=("detail",),
                post_assert=assert_resend,
            ),
            "bad_1": EndpointCase(
                "anonymous",
                "post",
                urls["users_resend_verification"],
                400,
                data={"email": users["verified"].email},
                format="json",
            ),
            "bad_2": EndpointCase(
                "anonymous",
                "post",
                urls["users_resend_verification"],
                404,
                data={"email": "ghost@example.com"},
                format="json",
            ),
        },
        "users_login": {
            "good": EndpointCase(
                "anonymous",
                "post",
                urls["users_login"],
                200,
                data={
                    "email": users["verified"].email,
                    "password": api_state["password"],
                },
                format="json",
                expected_keys=("email", "access", "refresh"),
                post_assert=assert_login,
            ),
            "bad_1": EndpointCase(
                "anonymous",
                "post",
                urls["users_login"],
                401,
                data={"email": users["verified"].email, "password": "wrong-pass"},
                format="json",
            ),
            "bad_2": EndpointCase(
                "verified",
                "post",
                urls["users_login"],
                405,
                data={
                    "email": users["verified"].email,
                    "password": api_state["password"],
                },
                format="json",
            ),
        },
        "users_logout": {
            "good": EndpointCase(
                "verified",
                "post",
                urls["users_logout"],
                200,
                data={},
                format="json",
                expected_keys=("detail",),
                setup=prepare_logout_refresh_token,
                post_assert=assert_logout,
                extra={"data_key": "logout_refresh"},
            ),
            "bad_1": EndpointCase(
                "verified",
                "post",
                urls["users_logout"],
                400,
                data={},
                format="json",
            ),
            "bad_2": EndpointCase(
                "anonymous",
                "post",
                urls["users_logout"],
                401,
                data={},
                format="json",
            ),
        },
        "users_language": {
            "good": EndpointCase(
                "verified",
                "post",
                urls["users_language"],
                200,
                data={"language": "en"},
                format="json",
                expected_keys=("language",),
                post_assert=assert_language,
            ),
            "bad_1": EndpointCase(
                "verified",
                "post",
                urls["users_language"],
                400,
                data={"language": "fr"},
                format="json",
            ),
            "bad_2": EndpointCase(
                "anonymous",
                "post",
                urls["users_language"],
                401,
                data={"language": "en"},
                format="json",
            ),
        },
        "hotels_create": {
            "good": EndpointCase(
                "owner",
                "post",
                urls["hotels_create"],
                201,
                data={"name": "Brand New Hotel", "rating": 5, "city": "Almaty"},
                format="json",
                expected_keys=("id", "name", "owner"),
                post_assert=assert_hotel_created,
            ),
            "bad_1": EndpointCase(
                "anonymous",
                "post",
                urls["hotels_create"],
                401,
                data={"name": "Anon Hotel"},
                format="json",
            ),
            "bad_2": EndpointCase(
                "owner",
                "post",
                urls["hotels_create"],
                400,
                data={"name": hotels["owner"].name},
                format="json",
            ),
        },
        "hotels_update": {
            "good": EndpointCase(
                "owner",
                "put",
                urls["hotels_update"],
                200,
                data={"name": "Renamed Hotel", "rating": 3},
                format="json",
                expected_keys=("id", "name", "owner"),
                post_assert=assert_hotel_updated,
            ),
            "bad_1": EndpointCase(
                "intruder",
                "put",
                urls["hotels_update"],
                403,
                data={"name": "Hijacked"},
                format="json",
            ),
            "bad_2": EndpointCase(
                "owner",
                "put",
                "/api/hotels/v1/hotels/999999/update",
                404,
                data={"name": "Missing Hotel"},
                format="json",
            ),
        },
        "hotels_detail": {
            "good": EndpointCase(
                "anonymous",
                "get",
                urls["hotels_detail"],
                200,
                expected_keys=("id", "name", "owner"),
                post_assert=assert_hotel_detail,
            ),
            "bad_1": EndpointCase(
                "anonymous",
                "get",
                "/api/hotels/v1/hotels/999999/details",
                404,
            ),
            "bad_2": EndpointCase(
                "anonymous",
                "post",
                urls["hotels_detail"],
                405,
                data={},
                format="json",
            ),
        },
        "hotels_list": {
            "good": EndpointCase(
                "anonymous",
                "get",
                urls["hotels_list"],
                200,
                expected_keys=("count", "results"),
                post_assert=assert_hotel_list,
            ),
            "bad_1": EndpointCase(
                "anonymous",
                "post",
                urls["hotels_list"],
                405,
                data={},
                format="json",
            ),
            "bad_2": EndpointCase(
                "anonymous",
                "delete",
                urls["hotels_list"],
                405,
            ),
        },
        "hotels_delete": {
            "good": EndpointCase(
                "owner",
                "delete",
                urls["hotels_delete"],
                204,
                post_assert=assert_hotel_deleted,
            ),
            "bad_1": EndpointCase("intruder", "delete", urls["hotels_delete"], 403),
            "bad_2": EndpointCase("anonymous", "delete", urls["hotels_delete"], 401),
        },
        "rooms_create": {
            "good": EndpointCase(
                "owner",
                "post",
                urls["rooms_create"],
                201,
                data={
                    "hotel": hotels["owner"].pk,
                    "title": "Suite",
                    "price_per_night": "200.00",
                    "capacity": 3,
                    "quantity": 2,
                },
                format="json",
                expected_keys=("id", "title", "hotel"),
                post_assert=assert_room_created,
            ),
            "bad_1": EndpointCase(
                "intruder",
                "post",
                urls["rooms_create"],
                403,
                data={
                    "hotel": hotels["owner"].pk,
                    "title": "Sneaky Room",
                    "price_per_night": "100.00",
                    "capacity": 2,
                },
                format="json",
            ),
            "bad_2": EndpointCase(
                "anonymous",
                "post",
                urls["rooms_create"],
                401,
                data={
                    "hotel": hotels["owner"].pk,
                    "title": "Anon Room",
                    "price_per_night": "100.00",
                    "capacity": 2,
                },
                format="json",
            ),
        },
        "rooms_update": {
            "good": EndpointCase(
                "owner",
                "put",
                urls["rooms_update"],
                200,
                data={
                    "hotel": hotels["owner"].pk,
                    "title": "Renamed Room",
                    "price_per_night": "120.00",
                    "capacity": 2,
                    "quantity": 1,
                },
                format="json",
                expected_keys=("id", "title", "hotel"),
                post_assert=assert_room_updated,
            ),
            "bad_1": EndpointCase(
                "intruder",
                "put",
                urls["rooms_update"],
                403,
                data={
                    "hotel": hotels["owner"].pk,
                    "title": "Hijacked",
                    "price_per_night": "100.00",
                    "capacity": 2,
                },
                format="json",
            ),
            "bad_2": EndpointCase(
                "owner",
                "put",
                "/api/hotels/v1/rooms/999999/update",
                404,
                data={
                    "hotel": hotels["owner"].pk,
                    "title": "Missing Room",
                    "price_per_night": "100.00",
                    "capacity": 2,
                    "quantity": 1,
                },
                format="json",
            ),
        },
        "rooms_detail": {
            "good": EndpointCase(
                "anonymous",
                "get",
                urls["rooms_detail"],
                200,
                expected_keys=("id", "title", "hotel"),
                post_assert=assert_room_detail,
            ),
            "bad_1": EndpointCase(
                "anonymous",
                "get",
                "/api/hotels/v1/rooms/999999/details",
                404,
            ),
            "bad_2": EndpointCase(
                "anonymous",
                "post",
                urls["rooms_detail"],
                405,
                data={},
                format="json",
            ),
        },
        "rooms_list": {
            "good": EndpointCase(
                "anonymous",
                "get",
                urls["rooms_list"],
                200,
                expected_keys=("count", "results"),
                post_assert=assert_room_list,
            ),
            "bad_1": EndpointCase(
                "anonymous",
                "post",
                urls["rooms_list"],
                405,
                data={},
                format="json",
            ),
            "bad_2": EndpointCase(
                "anonymous",
                "put",
                urls["rooms_list"],
                405,
                data={},
                format="json",
            ),
        },
        "rooms_delete": {
            "good": EndpointCase(
                "owner",
                "delete",
                urls["rooms_delete"],
                204,
                post_assert=assert_room_deleted,
            ),
            "bad_1": EndpointCase("intruder", "delete", urls["rooms_delete"], 403),
            "bad_2": EndpointCase("anonymous", "delete", urls["rooms_delete"], 401),
        },
        "reviews_list": {
            "good": EndpointCase(
                "anonymous",
                "get",
                urls["reviews_list"],
                200,
                expected_keys=("count", "results"),
                post_assert=assert_review_list,
            ),
            "bad_1": EndpointCase(
                "anonymous",
                "put",
                urls["reviews_list"],
                405,
                data={},
                format="json",
            ),
            "bad_2": EndpointCase("anonymous", "delete", urls["reviews_list"], 405),
        },
        "reviews_create": {
            "good": EndpointCase(
                "guest",
                "post",
                urls["reviews_create"],
                201,
                data={"rating": 5, "text": "Great stay"},
                format="json",
                expected_keys=("id", "hotel", "rating"),
                post_assert=assert_review_created,
            ),
            "bad_1": EndpointCase(
                "anonymous",
                "post",
                urls["reviews_create"],
                401,
                data={"rating": 4, "text": "Anon review"},
                format="json",
            ),
            "bad_2": EndpointCase(
                "reviewer",
                "post",
                urls["reviews_create"],
                400,
                data={"rating": 5, "text": "Second review"},
                format="json",
            ),
        },
        "bookings_create": {
            "good": EndpointCase(
                "guest",
                "post",
                urls["bookings_create"],
                201,
                data={
                    "room": rooms["review"].pk,
                    "check_in": dates["tomorrow"].isoformat(),
                    "check_out": dates["day_after"].isoformat(),
                },
                format="json",
                expected_keys=("id", "room", "status"),
                post_assert=assert_booking_created,
            ),
            "bad_1": EndpointCase(
                "guest",
                "post",
                urls["bookings_create"],
                400,
                data={
                    "room": rooms["review"].pk,
                    "check_in": dates["future_start"].isoformat(),
                    "check_out": dates["future_end"].isoformat(),
                },
                format="json",
            ),
            "bad_2": EndpointCase(
                "anonymous",
                "post",
                urls["bookings_create"],
                401,
                data={
                    "room": rooms["review"].pk,
                    "check_in": dates["tomorrow"].isoformat(),
                    "check_out": dates["day_after"].isoformat(),
                },
                format="json",
            ),
        },
        "bookings_list": {
            "good": EndpointCase(
                "guest",
                "get",
                urls["bookings_list"],
                200,
                expected_keys=("count", "results"),
                post_assert=assert_booking_list,
            ),
            "bad_1": EndpointCase("anonymous", "get", urls["bookings_list"], 401),
            "bad_2": EndpointCase(
                "guest",
                "post",
                urls["bookings_list"],
                405,
                data={},
                format="json",
            ),
        },
        "bookings_availability": {
            "good": EndpointCase(
                "guest",
                "get",
                urls["bookings_availability"],
                200,
                data={
                    "room": rooms["review"].pk,
                    "check_in": dates["tomorrow"].isoformat(),
                    "check_out": dates["day_after"].isoformat(),
                },
                expected_keys=("room", "check_in", "check_out", "available"),
                post_assert=assert_booking_availability,
            ),
            "bad_1": EndpointCase(
                "guest",
                "get",
                urls["bookings_availability"],
                400,
                data={
                    "room": rooms["review"].pk,
                    "check_in": dates["tomorrow"].isoformat(),
                    "check_out": dates["tomorrow"].isoformat(),
                },
            ),
            "bad_2": EndpointCase(
                "anonymous",
                "get",
                urls["bookings_availability"],
                401,
                data={
                    "room": rooms["review"].pk,
                    "check_in": dates["tomorrow"].isoformat(),
                    "check_out": dates["day_after"].isoformat(),
                },
            ),
        },
        "bookings_cancel": {
            "good": EndpointCase(
                "guest",
                "post",
                urls["bookings_cancel"],
                200,
                expected_keys=("id", "status", "check_in", "check_out", "total_price"),
                post_assert=assert_booking_cancel,
            ),
            "bad_1": EndpointCase(
                "other_guest",
                "post",
                urls["bookings_cancel"],
                403,
            ),
            "bad_2": EndpointCase(
                "guest",
                "post",
                "/api/bookings/v1/bookings/999999/cancel",
                404,
            ),
        },
    }
