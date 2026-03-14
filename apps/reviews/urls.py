from django.urls import path

from apps.reviews.views import HotelReviewViewSet

hotel_reviews = HotelReviewViewSet.as_view({"get": "list", "post": "create"})

urlpatterns = [
    path("hotels/<int:hotel_id>/reviews/", hotel_reviews, name="hotel-reviews"),
]
