# Python modules
from typing import Any

# from datetime import datetime, timezone

# Django modules
from django.db.models import Model, DateTimeField
from django.utils import timezone


class AbstractBaseModel(Model):
    """
    Abstract base model with common fields.
    """

    created_at = DateTimeField(
        default=timezone.now
    )
    updated_at = DateTimeField(
        default=timezone.now
    )
    

    class Meta:
        """Meta class for AbstractBaseModel."""

        abstract = True

class AbstractSoftDeleteModel(Model):
    """
    Abstract base model with soft delete functionality.
    """

    deleted_at = DateTimeField(
        blank=True,
        null=True,
        default=None
    )

    def delete(self, *args: tuple[Any, ...], **kwargs: dict[Any, Any]) -> None:
        """Soft delete the object by setting deleted_at timestamp."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def restore(self) -> None:
        """Restore the soft-deleted object by clearing deleted_at."""
        self.deleted_at = None
        self.save()