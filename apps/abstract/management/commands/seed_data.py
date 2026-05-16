# Python modules
from datetime import datetime, timedelta
from random import choice, randint, uniform
from typing import Any

from django.core.management.base import BaseCommand

# Django modules
from django.utils import timezone

from apps.bookings.models import Booking, BookingStatus
from apps.hotels.models import Hotel
from apps.reviews.models import Review
from apps.rooms.models import Room

# Project modules
from apps.users.models import User


class Command(BaseCommand):
    """Generate test data for hotel booking system."""

    help = "Generate users, hotels, rooms, bookings and reviews."

    FIRST_NAMES = (
        "Alice",
        "Bob",
        "Charlie",
        "Diana",
        "Eve",
        "Frank",
        "Grace",
        "Ivan",
        "John",
        "Oliver",
        "Lucas",
        "Daniel",
        "Michael",
        "Ethan",
        "Samuel",
        "Henry",
        "David",
    )

    LAST_NAMES = (
        "Smith",
        "Johnson",
        "Brown",
        "Williams",
        "Miller",
        "Davis",
        "Wilson",
        "Moore",
        "Taylor",
        "Anderson",
    )

    EMAIL_DOMAINS = ("gmail.com", "mail.com", "example.com", "kbtu.kz", "test.com")

    HOTEL_NAMES = (
        "Grand Hotel",
        "Sunrise Resort",
        "Golden Palace",
        "Ocean View",
        "Royal Garden",
        "Skyline Hotel",
        "City Comfort",
        "Luxury Stay",
    )

    CITIES = ("Almaty", "Astana", "Shymkent", "Aktau", "Atyrau", "Karaganda")

    ROOM_TITLES = (
        "Standard Room",
        "Deluxe Room",
        "Family Suite",
        "Luxury Suite",
        "Single Room",
        "Double Room",
    )

    REVIEW_TEXTS = (
        "Great hotel and friendly staff.",
        "Very clean and comfortable stay.",
        "Amazing location and service.",
        "Would definitely visit again.",
        "Nice experience overall.",
        "Good value for money.",
    )

    STATUSES = (
        BookingStatus.PENDING,
        BookingStatus.CONFIRMED,
        BookingStatus.CANCELLED,
        BookingStatus.COMPLETED,
    )

    def _write_created_total(
        self,
        entity_name: str,
        before_count: int,
        after_count: int,
    ) -> None:
        """Print how many rows were created for a seeded entity."""
        self.stdout.write(
            self.style.SUCCESS(f"Created {after_count - before_count} {entity_name}")
        )

    def _generate_users(self, count: int = 50) -> None:
        """Generate a batch of users with random names and email domains."""

        users_before = User.objects.count()
        users: list[User] = []

        for i in range(count):

            first_name = choice(self.FIRST_NAMES)
            last_name = choice(self.LAST_NAMES)

            users.append(
                User(
                    email=f"user{i}@{choice(self.EMAIL_DOMAINS)}",
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                    is_staff=False,
                    created_at=timezone.now(),
                )
            )

        User.objects.bulk_create(users, ignore_conflicts=True)

        self._write_created_total("users", users_before, User.objects.count())

    def _generate_hotels(self, count: int = 20) -> None:
        """Generate a batch of hotels owned by existing users."""

        users = list(User.objects.all())

        hotels_before = Hotel.objects.count()
        hotels: list[Hotel] = []

        for _ in range(count):

            owner = choice(users)

            hotels.append(
                Hotel(
                    owner=owner,
                    name=choice(self.HOTEL_NAMES),
                    city=choice(self.CITIES),
                    address=f"{randint(1,200)} Main Street",
                    rating=randint(1, 5),
                    description="Nice hotel with great service.",
                    created_at=timezone.now(),
                )
            )

        Hotel.objects.bulk_create(hotels, ignore_conflicts=True)

        self._write_created_total("hotels", hotels_before, Hotel.objects.count())

    def _generate_rooms(self, count_per_hotel: int = 5) -> None:
        """Generate a set of rooms for each hotel."""

        hotels = list(Hotel.objects.all())

        rooms_before = Room.objects.count()
        rooms: list[Room] = []

        for hotel in hotels:

            for _ in range(count_per_hotel):

                rooms.append(
                    Room(
                        hotel=hotel,
                        title=choice(self.ROOM_TITLES),
                        price_per_night=round(uniform(40, 300), 2),
                        capacity=randint(1, 4),
                        quantity=randint(1, 10),
                        created_at=timezone.now(),
                    )
                )

        Room.objects.bulk_create(rooms, ignore_conflicts=True)

        self._write_created_total("rooms", rooms_before, Room.objects.count())

    def _generate_bookings(self, count: int = 50) -> None:
        """Generate a batch of bookings across existing users and rooms."""

        users = list(User.objects.all())
        rooms = list(Room.objects.all())

        bookings_before = Booking.objects.count()
        bookings: list[Booking] = []

        for _ in range(count):

            user = choice(users)
            room = choice(rooms)

            check_in = datetime.now().date() + timedelta(days=randint(1, 30))
            nights = randint(1, 7)
            check_out = check_in + timedelta(days=nights)

            total_price = nights * float(room.price_per_night)

            bookings.append(
                Booking(
                    user=user,
                    room=room,
                    check_in=check_in,
                    check_out=check_out,
                    status=choice(self.STATUSES),
                    total_price=total_price,
                    created_at=timezone.now(),
                )
            )

        Booking.objects.bulk_create(bookings, ignore_conflicts=True)

        self._write_created_total("bookings", bookings_before, Booking.objects.count())

    def _generate_reviews(self, count: int = 40) -> None:
        """Generate a batch of reviews across existing users and hotels."""

        users = list(User.objects.all())
        hotels = list(Hotel.objects.all())

        reviews_before = Review.objects.count()
        reviews: list[Review] = []

        for _ in range(count):

            reviews.append(
                Review(
                    user=choice(users),
                    hotel=choice(hotels),
                    rating=randint(1, 5),
                    text=choice(self.REVIEW_TEXTS),
                    created_at=timezone.now(),
                )
            )

        Review.objects.bulk_create(reviews, ignore_conflicts=True)

        self._write_created_total("reviews", reviews_before, Review.objects.count())

    def handle(self, *args: tuple[Any], **kwargs: dict[str, Any]) -> None:
        """Populate the database with a representative set of sample data."""

        start_time = datetime.now()

        self._generate_users()
        self._generate_hotels()
        self._generate_rooms()
        self._generate_bookings()
        self._generate_reviews()

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished seeding in {(datetime.now() - start_time).total_seconds()} seconds"
            )
        )
