from typing import Any

from rest_framework import serializers

from apps.rooms.models import Room


class RoomCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating a room."""
    class Meta:
        """Meta options for the RoomCreateUpdateSerializer."""
        model = Room
        fields = ("id", "hotel", "title", "price_per_night", "capacity", "quantity")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Custom validation to ensure price, capacity, and quantity are positive."""
        price = attrs.get("price_per_night")
        capacity = attrs.get("capacity")
        quantity = attrs.get("quantity")
        if price is not None and price <= 0:
            raise serializers.ValidationError({"price_per_night": "Must be positive."})
        if capacity is not None and capacity <= 0:
            raise serializers.ValidationError({"capacity": "Must be > 0."})
        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError({"quantity": "Must be > 0."})
        return attrs


class RoomDetailSerializer(serializers.ModelSerializer):
    """Serializer for retrieving room details."""
    class Meta:
        """Meta options for the RoomDetailSerializer."""
        model = Room
        fields = (
            "id",
            "hotel",
            "title",
            "price_per_night",
            "capacity",
            "quantity",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

