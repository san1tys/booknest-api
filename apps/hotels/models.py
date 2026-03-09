from typing import Any
from django.db import models
from django.forms import ValidationError
from apps.abstract.models import AbstractBaseModel


def validate_rating(value: int):
    """Validator to ensure that the rating is between 1 and 5."""
    if value < 1 or value > 5:
        raise ValidationError('Rating must be between 1 and 5.')

class Hotel(AbstractBaseModel):
    """Model representing a hotel."""

    NAME_MAX_LENGTH = 255
    ADDRESS_MAX_LENGTH = 255
    CITY_MAX_LENGTH = 100

    name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        error_messages={
            'unique': "A hotel with this name already exists. Please choose a different name."
        },
        verbose_name="Hotel Name",
        help_text="Enter the name of the hotel.",
        null=False,
        blank=False,
        )   
    address = models.CharField(
        max_length=ADDRESS_MAX_LENGTH,
        verbose_name="Hotel Address",
        help_text="Enter the address of the hotel.",
        null=True,
        blank=True,
        )
    city = models.CharField(
        max_length=CITY_MAX_LENGTH,
        verbose_name="Hotel City",
        help_text="Enter the city where the hotel is located.",
        null=True,
        blank=True,
        )
    rating = models.IntegerField(
        verbose_name="Hotel Rating",
        help_text="Enter the rating of the hotel (1-5).",
        null=True,
        blank=True,
        # validators=[validate_rating],
        # default=1,
        )
    description = models.TextField(
        verbose_name="Hotel Description",
        help_text="Enter a description of the hotel.",
        null=True,
        blank=True,
    )

    owner = models.ForeignKey(
        to='users.User',
        on_delete=models.CASCADE,
        related_name='hotels',
        verbose_name="Hotel Owner",
        help_text="Select the owner of the hotel.",
        null=True,
        blank=True,
    )

    def clean(self) -> None:
        """Custom validation to ensure that the rating is between 1 and 5."""
        if self.rating is not None and (self.rating < 1 or self.rating > 5):
            raise ValidationError('Rating must be between 1 and 5.')
        return super().clean()

    def save(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

#Room

class Room(AbstractBaseModel):
    """Room inside a hotel."""

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

    def clean(self) -> None:
        if self.price_per_night is not None and self.price_per_night <= 0:
            raise ValidationError("price_per_night must be positive.")
        if self.capacity is not None and self.capacity <= 0:
            raise ValidationError("capacity must be > 0.")
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError("quantity must be > 0.")
        return super().clean()

    def save(
        self, *args: tuple[Any, ...], **kwargs: dict[str, Any]
    ) -> None:
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.title} @ {self.hotel.name}"