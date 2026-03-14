from typing import Any

from django.db.models import Q
from rest_framework import serializers

from apps.bookings.models import Booking, BookingStatus


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new booking."""

    class Meta:
        """Meta options for the BookingCreateSerializer."""

        model = Booking
        fields = ("id", "room", "check_in", "check_out", "status", "total_price")
        read_only_fields = ("id", "status", "total_price")

    def validate(self, attrs: dict) -> dict:
        """Custom validation to check room availability and date consistency."""
        room = attrs["room"]
        check_in = attrs["check_in"]
        check_out = attrs["check_out"]

        if check_out <= check_in:
            raise serializers.ValidationError(
                {"check_out": "Check-out date must be after check-in date."}
            )

        overlapping_bookings = Booking.objects.filter(
            room=room,
            status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
        ).filter(Q(check_in__lt=check_out) & Q(check_out__gt=check_in))

        if overlapping_bookings.exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": "The selected room is not available for the chosen dates."
                }
            )

        return attrs

    def create(self, validated_data: dict[str, Any]) -> Booking:
        """Override the create method to calculate total price and set the user from the request."""
        request = self.context["request"]
        room = validated_data["room"]
        check_in = validated_data["check_in"]
        check_out = validated_data["check_out"]

        nights = (check_out - check_in).days
        total_price = room.price_per_night * nights

        booking = Booking.objects.create(
            user=request.user,
            room=room,
            check_in=check_in,
            check_out=check_out,
            total_price=total_price,
            status=BookingStatus.PENDING,
        )
        return booking


class BookingListSerializer(serializers.ModelSerializer):
    """Serializer for listing bookings with related user email, room title, and hotel name."""

    user_email = serializers.EmailField(source="user.email", read_only=True)
    room_title = serializers.CharField(source="room.title", read_only=True)
    hotel_name = serializers.CharField(source="room.hotel.name", read_only=True)

    class Meta:
        model = Booking
        fields = (
            "id",
            "user_email",
            "room",
            "room_title",
            "hotel_name",
            "check_in",
            "check_out",
            "status",
            "total_price",
            "created_at",
        )


class AvailabilityQuerySerializer(serializers.Serializer):
    """Serializer for validating availability check query parameters."""

    room = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["check_out"] <= attrs["check_in"]:
            raise serializers.ValidationError(
                {"check_out": "Check-out date must be after check-in date."}
            )
        return attrs


class AvailabilityResponseSerializer(serializers.Serializer):
    """Serializer for returning availability check results."""

    room = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    available = serializers.BooleanField()


class BookingCancelSerializer(serializers.ModelSerializer):
    """Serializer for cancelling a booking, allowing only the status field to be updated."""

    class Meta:
        """Meta options for the BookingCancelSerializer."""

        model = Booking
        fields = ("id", "status", "check_in", "check_out", "total_price")
        read_only_fields = fields
