from typing import Any

from django.db import models
from django.forms import ValidationError

from apps.abstract.models import AbstractBaseModel


class Room(AbstractBaseModel):
    """
    Room inside a hotel.

    ## args:
        hotel (Hotel): The hotel this room belongs to.
        title (str): The title of the room.
        price_per_night (Decimal): The price per night for this room.
        capacity (int): The maximum number of guests this room can accommodate.
        quantity (int): The number of identical rooms of this type available in the hotel.
    """

    TITLE_MAX_LENGTH = 255

    hotel = models.ForeignKey(
        "hotels.Hotel",
        on_delete=models.CASCADE,
        related_name="rooms",
        verbose_name="Hotel",
        help_text="Parent hotel.",
    )
    title = models.CharField(
        max_length=TITLE_MAX_LENGTH,
        verbose_name="Room title",
        help_text='e.g. "Deluxe Room"',
    )
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Price per night",
        help_text="Decimal price per night.",
    )
    capacity = models.PositiveIntegerField(
        verbose_name="Capacity",
        help_text="Guests count this room type can host.",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Quantity",
        help_text="How many identical rooms of this type exist.",
    )

    class Meta:
        ordering = ["-created_at"]
        db_table = "hotels_room"

    def clean(self) -> None:
        if self.price_per_night is not None and self.price_per_night <= 0:
            raise ValidationError("price_per_night must be positive.")
        if self.capacity is not None and self.capacity <= 0:
            raise ValidationError("capacity must be > 0.")
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError("quantity must be > 0.")
        return super().clean()

    def save(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.title} @ {self.hotel.name}"
