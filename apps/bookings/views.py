from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics, status
from django.db.models import Q, QuerySet
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

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
    
class AvailabilityView(APIView):
    permission_classes = (IsAuthenticated,)
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="room",
                required=True,
                type=int,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="check_in",
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="check_out",
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={200:AvailabilityResponseSerializer}    
    )
    
    def get(self, request, *args, **kwargs) -> Response:
        query_serializer = AvailabilityQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        room = query_serializer.validated_data["room"]
        check_in = query_serializer.validated_data["check_in"]
        check_out = query_serializer.validated_data["check_out"]
        
        overlapping_bookings = Booking.objects.filter(
            room_id=room,
            status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
        ).filter(
            Q(check_in__lt=check_out) & Q(check_out__gt=check_in)
        )
        
        data = {
            "room": room,
            "check_in": check_in,
            "check_out": check_out,
            "available": not overlapping_bookings.exists()
        }
        
        response_serializer = AvailabilityResponseSerializer(data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
            
class BookingCancelView(APIView):
    permission_classes = (IsAuthenticated,)   
    
    def post(self, request, pk: int, *args, **kwargs) -> Response:
        try:
            booking = Booking.objects.select_related(
                "user",
                "room",
                "room__hotel",
                "room__hotel__owner"
            ).get(pk=pk)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)
        
        is_booking_owner = booking.user == request.user
        is_hotel_owner = booking.room.hotel.owner == request.user
        
        if not (is_booking_owner or is_hotel_owner):
            return Response({"detail": "You do not have permission to cancel this booking."}, status=status.HTTP_403_FORBIDDEN)
        
        booking.status = BookingStatus.CANCELLED
        booking.save()
        
        serializer = BookingCancelSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)
            