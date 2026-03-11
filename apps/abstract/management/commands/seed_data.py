# Python modules
from typing import Any, List, Dict, Tuple
from random import choice, randint, uniform
from datetime import datetime, timedelta

# Django modules
from django.utils import timezone
from django.core.management.base import BaseCommand

# Project modules
from apps.users.models import User
from apps.hotels.models import Hotel
from apps.bookings.models import Booking
from apps.rooms.models import Room
from apps.reviews.models import Review


class Command(BaseCommand):
    """Generate test data for hotel booking system."""

    help = "Generate users, hotels, rooms, bookings and reviews."

    FIRST_NAMES = (
        "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank",
        "Grace", "Ivan", "John", "Oliver", "Lucas", "Daniel",
        "Michael", "Ethan", "Samuel", "Henry", "David"
    )

    LAST_NAMES = (
        "Smith", "Johnson", "Brown", "Williams", "Miller",
        "Davis", "Wilson", "Moore", "Taylor", "Anderson"
    )

    EMAIL_DOMAINS = (
        "gmail.com",
        "mail.com",
        "example.com",
        "kbtu.kz",
        "test.com"
    )

    HOTEL_NAMES = (
        "Grand Hotel",
        "Sunrise Resort",
        "Golden Palace",
        "Ocean View",
        "Royal Garden",
        "Skyline Hotel",
        "City Comfort",
        "Luxury Stay"
    )

    CITIES = (
        "Almaty",
        "Astana",
        "Shymkent",
        "Aktau",
        "Atyrau",
        "Karaganda"
    )

    ROOM_TITLES = (
        "Standard Room",
        "Deluxe Room",
        "Family Suite",
        "Luxury Suite",
        "Single Room",
        "Double Room"
    )

    REVIEW_TEXTS = (
        "Great hotel and friendly staff.",
        "Very clean and comfortable stay.",
        "Amazing location and service.",
        "Would definitely visit again.",
        "Nice experience overall.",
        "Good value for money."
    )

    STATUSES = (
        "pending",
        "confirmed",
        "canceled",
        "completed"
    )

    # ---------------- USERS ---------------- #

    def __generate_users(self, count: int = 50) -> None:

        users_before = User.objects.count()
        users: List[User] = []

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
                    created_at=timezone.now()
                )
            )

        User.objects.bulk_create(users, ignore_conflicts=True)

        users_after = User.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {users_after - users_before} users"
            )
        )

    # ---------------- HOTELS ---------------- #

    def __generate_hotels(self, count: int = 20) -> None:

        users = list(User.objects.all())

        hotels_before = Hotel.objects.count()
        hotels: List[Hotel] = []

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
                    created_at=timezone.now()
                )
            )

        Hotel.objects.bulk_create(hotels, ignore_conflicts=True)

        hotels_after = Hotel.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {hotels_after - hotels_before} hotels"
            )
        )

    # ---------------- ROOMS ---------------- #

    def __generate_rooms(self, count_per_hotel: int = 5) -> None:

        hotels = list(Hotel.objects.all())

        rooms_before = Room.objects.count()
        rooms: List[Room] = []

        for hotel in hotels:

            for _ in range(count_per_hotel):

                rooms.append(
                    Room(
                        hotel=hotel,
                        title=choice(self.ROOM_TITLES),
                        price_per_night=round(uniform(40, 300), 2),
                        capacity=randint(1, 4),
                        quantity=randint(1, 10),
                        created_at=timezone.now()
                    )
                )

        Room.objects.bulk_create(rooms, ignore_conflicts=True)

        rooms_after = Room.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {rooms_after - rooms_before} rooms"
            )
        )

    # ---------------- BOOKINGS ---------------- #

    def __generate_bookings(self, count: int = 50) -> None:

        users = list(User.objects.all())
        rooms = list(Room.objects.all())

        bookings_before = Booking.objects.count()
        bookings: List[Booking] = []

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
                    created_at=timezone.now()
                )
            )

        Booking.objects.bulk_create(bookings, ignore_conflicts=True)

        bookings_after = Booking.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {bookings_after - bookings_before} bookings"
            )
        )

    # ---------------- REVIEWS ---------------- #

    def __generate_reviews(self, count: int = 40) -> None:

        users = list(User.objects.all())
        hotels = list(Hotel.objects.all())

        reviews_before = Review.objects.count()
        reviews: List[Review] = []

        for _ in range(count):

            reviews.append(
                Review(
                    user=choice(users),
                    hotel=choice(hotels),
                    rating=randint(1, 5),
                    text=choice(self.REVIEW_TEXTS),
                    created_at=timezone.now()
                )
            )

        Review.objects.bulk_create(reviews, ignore_conflicts=True)

        reviews_after = Review.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {reviews_after - reviews_before} reviews"
            )
        )

    # ---------------- HANDLE ---------------- #

    def handle(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:

        start_time = datetime.now()

        self.__generate_users()
        self.__generate_hotels()
        self.__generate_rooms()
        self.__generate_bookings()
        self.__generate_reviews()

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished seeding in {(datetime.now() - start_time).total_seconds()} seconds"
            )
        )
