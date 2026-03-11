from typing import Any

from django.db import models
from django.forms import ValidationError

from apps.abstract.models import AbstractBaseModel


class BookingStatus(models.TextChoices):
    """Enumeration of possible booking statuses."""
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Booking(AbstractBaseModel):
    """
    Model representing a hotel room booking.

    args:
        user (User): The user who made the booking.
        room (Room): The room that is booked.
        check_in (date): The date when the booking starts.
        check_out (date): The date when the booking ends.
        status (str): The current status of the booking (e.g., pending, confirmed, cancelled).
        total_price (Decimal): The total price for the booking.
    relationships:
        user (User): Foreign key to the User model, representing the user who made the booking.
        room (Room): Foreign key to the Room model, representing the room that is booked.
    """

    STATUS_MAX_LENGTH = 20

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="User",
        help_text="The user who made the booking.",
    )
    room = models.ForeignKey(
        "hotels.Room",
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="Room",
        help_text="The room that is booked.",
    )
    check_in = models.DateField(
        verbose_name="Check-in Date", help_text="The date when the booking starts."
    )
    check_out = models.DateField(
        verbose_name="Check-out Date", help_text="The date when the booking ends."
    )
    status = models.CharField(
        max_length=STATUS_MAX_LENGTH,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
        verbose_name="Booking Status",
        help_text="The current status of the booking (e.g., pending, confirmed, cancelled).",
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total Price",
        help_text="The total price for the booking.",
        default=0.00,
    )

    class Meta:
        """Meta options for the Booking model."""
        ordering = ["-created_at"]

    def clean(self) -> None:
        """Custom validation to ensure check-out date is after check-in date."""
        if self.check_in and self.check_out and self.check_out <= self.check_in:
            raise ValidationError("Check-out date must be after check-in date.")
        return super().clean()

    def save(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
        """Override save method to perform validation before saving the booking instance."""
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return a string representation of the booking, including user, room, and dates."""
        return f"Booking {self.id} by {self.user} for {self.room} from {self.check_in} to {self.check_out}"
