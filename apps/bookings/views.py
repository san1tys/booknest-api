from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics
from django.db.models import Q, QuerySet

from apps.bookings.models import Booking
from apps.bookings.serializers import *

class BookingCreateView(generics.CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingCreateSerializer
    permission_classes = (IsAuthenticated)
    
class BookingListView(generics.ListAPIView):
    serializer_class = BookingListSerializer
    permission_classes = (IsAuthenticated)
    
    def get_queryset(self) -> QuerySet[Booking]:
        user = self.request.user
        
        queryset = Booking.objects.select_related(
            "user",
            "room",
            "room__hotel",
            "room__hotel__owner"
        ).order_by("-created_at")
        
        if user.hotels.exists():
            return queryset.filter(room__hotel__owner=user)
        return queryset.filter(user=user)    
            