from django.urls import path

from apps.bookings.views import BookingCreateView

urlpatterns = [
    path("bookings/", BookingCreateView.as_view(), name="booking-create"),
]