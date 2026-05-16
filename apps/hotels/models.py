from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.abstract.models import AbstractBaseModel

# def validate_rating(value: int):
#     """Validator to ensure that the rating is between 1 and 5."""
#     if value < 1 or value > 5:
#         raise ValidationError("Rating must be between 1 and 5.")


class Hotel(AbstractBaseModel):
    """
    Model representing a hotel.

    args:
        name (str): The name of the hotel.
        address (str): The address of the hotel.
        city (str): The city where the hotel is located.
        rating (int): The rating of the hotel (1-5).
        description (str): A description of the hotel.

    relationships:
        owner (User): The user who owns the hotel.
    """

    NAME_MAX_LENGTH = 255
    ADDRESS_MAX_LENGTH = 255
    CITY_MAX_LENGTH = 100

    name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        error_messages={
            "unique": _(
                "A hotel with this name already exists. Please choose a "
                "different name."
            )
        },
        verbose_name=_("Hotel Name"),
        help_text=_("Enter the name of the hotel."),
        null=False,
        blank=False,
    )
    address = models.CharField(
        max_length=ADDRESS_MAX_LENGTH,
        verbose_name=_("Hotel Address"),
        help_text=_("Enter the address of the hotel."),
        null=True,
        blank=True,
    )
    city = models.CharField(
        max_length=CITY_MAX_LENGTH,
        verbose_name=_("Hotel City"),
        help_text=_("Enter the city where the hotel is located."),
        null=True,
        blank=True,
    )
    rating = models.IntegerField(
        verbose_name=_("Hotel Rating"),
        help_text=_("Enter the rating of the hotel (1-5)."),
        null=True,
        blank=True,
    )
    description = models.TextField(
        verbose_name=_("Hotel Description"),
        help_text=_("Enter a description of the hotel."),
        null=True,
        blank=True,
    )

    owner = models.ForeignKey(
        to="users.User",
        on_delete=models.CASCADE,
        related_name="hotels",
        verbose_name=_("Hotel Owner"),
        help_text=_("Select the owner of the hotel."),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Hotel")
        verbose_name_plural = _("Hotels")

    def clean(self) -> None:
        """Custom validation to ensure that the rating is between 1 and 5."""
        if self.rating is not None and (self.rating < 1 or self.rating > 5):
            raise ValidationError(_("Rating must be between 1 and 5."))
        return super().clean()

    def save(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name
