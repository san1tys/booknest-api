from rest_framework import serializers

from apps.reviews.models import Review


class ReviewListSerializer(serializers.ModelSerializer):
    """Serializer for listing reviews with user email."""

    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        """Meta options for the ReviewListSerializer."""

        model = Review
        fields = ("id", "hotel", "user_email", "rating", "text", "created_at")
        read_only_fields = ("id", "hotel", "user_email", "created_at")


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new review."""

    class Meta:
        """Meta options for the ReviewCreateSerializer."""

        model = Review
        fields = ("rating", "text")
