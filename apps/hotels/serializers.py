from typing import Any

from rest_framework import serializers

from apps.hotels.models import Hotel
from apps.users.models import User
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

