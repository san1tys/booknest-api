from typing import Any

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

from apps.abstract.models import AbstractBaseModel, AbstractSoftDeleteModel

class UserManager(BaseUserManager):
    """Custom user manager to handle user creation and superuser creation using email as the unique identifier."""
    
    def create_user(self, email: str, password: str | None = None, **extra_fields: dict[str, Any]):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields: dict[str, Any]):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin, AbstractBaseModel, AbstractSoftDeleteModel):
    """Custom user model using email as the unique identifier, with additional fields for first name, last name, and account status."""

    NAME_LENGTH = 100

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=NAME_LENGTH, blank=True)
    last_name = models.CharField(max_length=NAME_LENGTH, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        """Return the string representation of the user, which is their email address."""
        return self.email