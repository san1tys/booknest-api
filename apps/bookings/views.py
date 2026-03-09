from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics

from apps.bookings.models import Booking
from apps.bookings.serializers import BookingCreateSerializer

class BookingCreateView(generics.CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingCreateSerializer
    permission_classes = (IsAuthenticated)