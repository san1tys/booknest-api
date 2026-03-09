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