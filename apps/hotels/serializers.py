from typing import Any
from rest_framework import serializers
from apps.hotels.models import Hotel, Room
from apps.users.serializers import UserSerializer

class HotelSerializer(serializers.ModelSerializer):
    """Serializer for Hotel model, including all fields."""
    class Meta:
        """Meta class for HotelSerializer."""
        model = Hotel
        fields = "__all__"

class HotelCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating Hotel instances, including all fields."""
    class Meta:
        """Meta class for HotelCreateUpdateSerializer."""
        model = Hotel
        fields = "__all__"
    
    def create(self, validated_data: dict[str, Any]) -> Hotel:
        """Create a new Hotel instance with the provided validated data."""
        return Hotel.objects.create(**validated_data)

    def update(self, instance: Hotel, validated_data: dict[str, Any]) -> Hotel:
        """Update an existing Hotel instance with the provided validated data."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class HotelDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed view of Hotel instances, including all fields."""
    owner = UserSerializer(read_only=True)

    class Meta:
        """Meta class for HotelDetailSerializer."""
        model = Hotel
        fields = ["id", "name", "description", "address", "city", "created_at", "owner"]

# class HotelDeleteSerializer(serializers.ModelSerializer):
#     """Serializer for deleting Hotel instances, including only the id field."""

#     class Meta:
#         """Meta class for HotelDeleteSerializer."""
#         model = Hotel
#         fields = ["id"]

#     def delete(self, instance: Hotel) -> None:
#         """Delete the specified Hotel instance."""
#         instance.delete()




class RoomCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ("id", "hotel", "title", "price_per_night", "capacity", "quantity")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
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
    class Meta:
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