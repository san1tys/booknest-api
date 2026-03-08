# apps/common/serializers.py
from rest_framework import serializers


class ErrorDetailSerializer(serializers.Serializer):
    """Serializer for error details."""
    detail = serializers.CharField()


class ValidationErrorSerializer(serializers.Serializer):
    """Error serializer for validation errors."""
    errors = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField())
    )


class MessageSerializer(serializers.Serializer):
    """Serializer for simple message responses."""
    detail = serializers.CharField()