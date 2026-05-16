from django.urls import path

from apps.bookings.consumers import BookingStatusConsumer

websocket_urlpatterns = [
    path("ws/bookings/", BookingStatusConsumer.as_asgi()),
]
