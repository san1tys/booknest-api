from rest_framework import serializers

from apps.hotels.models import Hotel
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
        exclude = ("owner",)


class HotelDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed view of Hotel instances, including all fields."""

    owner = UserSerializer(read_only=True)

    class Meta:
        """Meta class for HotelDetailSerializer."""

        model = Hotel
        fields = [
            "id",
            "name",
            "description",
            "address",
            "city",
            "created_at",
            "owner",
            "rating",
        ]
