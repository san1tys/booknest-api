from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.abstract.models import AbstractBaseModel


class Review(AbstractBaseModel):
    """
    Model representing a review of a hotel by a user.

    ## args:
        hotel (Hotel): The hotel being reviewed.
        rating (int): The rating given to the hotel (1-5).
        text (str): The text of the review.
    """

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="reviews"
    )
    hotel = models.ForeignKey(
        "hotels.Hotel", on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField(blank=True)

    class Meta:
        unique_together = ("user", "hotel")
        ordering = ("-created_at",)
        db_table = "hotels_review"

    def __str__(self) -> str:
        return f"Review({self.user.email} -> {self.hotel.name}, {self.rating})"

