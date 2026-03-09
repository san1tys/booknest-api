from django.urls import path

from apps.bookings.views import *

urlpatterns = [
    path("bookings/", BookingListView.as_view(), name="booking-list"),
    path("bookings/create/", BookingCreateView.as_view(), name="booking-create"),
]