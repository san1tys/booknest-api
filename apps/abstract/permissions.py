from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.viewsets import ViewSet

from apps.hotels.models import Hotel


class IsOwner(BasePermission):
    """Custom permission to only allow owners of an object to access it."""

    message = "You must be the owner of this Hotel to access it."

    def has_object_permission(self, request: Any, view: ViewSet, obj: Hotel) -> bool:
        """Check if the user is the owner of the object."""
        if isinstance(obj, Hotel):  # Assuming obj is a Hotel instance
            return obj.owner == request.user
        if isinstance(obj, int):  # Assuming obj is hotel_id
            try:
                hotel: Hotel = Hotel.objects.get(id=obj)
                return hotel.owner == request.user
            except Hotel.DoesNotExist:
                return False
        return False
