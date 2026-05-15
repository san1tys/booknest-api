from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.abstract.models import AbstractBaseModel


class Room(AbstractBaseModel):
    TITLE_MAX_LENGTH = 255

    hotel = models.ForeignKey(
        "hotels.Hotel",
        on_delete=models.CASCADE,
        related_name="rooms",
        verbose_name=_("Hotel"),
        help_text=_("Parent hotel."),
    )
    title = models.CharField(
        max_length=TITLE_MAX_LENGTH,
        verbose_name=_("Room title"),
        help_text=_('e.g. "Deluxe Room"'),
    )
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Price per night"),
        help_text=_("Decimal price per night."),
    )
    capacity = models.PositiveIntegerField(
        verbose_name=_("Capacity"),
        help_text=_("Guests count this room type can host."),
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Quantity"),
        help_text=_("How many identical rooms of this type exist."),
    )

    class Meta:
        ordering = ["-created_at"]
        db_table = "hotels_room"
        verbose_name = _("Room")
        verbose_name_plural = _("Rooms")

    def clean(self) -> None:
        if self.price_per_night is not None and self.price_per_night <= 0:
            raise ValidationError(_("Price per night must be positive."))
        if self.capacity is not None and self.capacity <= 0:
            raise ValidationError(_("Capacity must be greater than 0."))
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError(_("Quantity must be greater than 0."))
        return super().clean()

    def save(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.title} @ {self.hotel.name}"