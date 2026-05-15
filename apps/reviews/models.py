from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.abstract.models import AbstractBaseModel


class Review(AbstractBaseModel):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("User"),
    )
    hotel = models.ForeignKey(
        "hotels.Hotel",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("Hotel"),
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Rating"),
    )
    text = models.TextField(blank=True, verbose_name=_("Review text"))

    class Meta:
        unique_together = ("user", "hotel")
        ordering = ("-created_at",)
        db_table = "hotels_review"
        verbose_name = _("Review")
        verbose_name_plural = _("Reviews")

    def __str__(self) -> str:
        return f"Review({self.user.email} -> {self.hotel.name}, {self.rating})"