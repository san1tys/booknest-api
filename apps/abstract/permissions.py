from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.viewsets import ViewSet


class IsOwner(BasePermission):
    """Custom permission to only allow owners of an object to access it."""

    message = "You must be the owner of this object to access it."

    def has_object_permission(self, request: Any, view: ViewSet, obj: Any) -> bool:
        """Return whether the request user owns the provided object."""
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        if hasattr(obj, "user"):
            return obj.user == request.user
        return False
