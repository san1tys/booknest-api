from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.users.models import User
from apps.users.services import (
    get_email_verification_otp,
    set_email_verification_otp,
)
from apps.users.tasks import send_OTP as send_email


LOC_MEM_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "users-otp-tests",
    }
}


@override_settings(
    CACHES=LOC_MEM_CACHES,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class UserOtpFlowTests(TestCase):
    """Tests for registration and email verification OTP flow."""

    def setUp(self) -> None:
        """Prepare a clean API client and cache state for each test."""
        cache.clear()
        self.client = APIClient()
        self.register_url = "/api/users/v1/users/register"
        self.login_url = "/api/users/v1/users/login"
        self.verify_url = "/api/users/v1/users/verify-email"
        self.resend_url = "/api/users/v1/users/resend-verification"

    @patch("apps.users.services.send_email.delay")
    def test_register_creates_unverified_user_and_queues_otp(
        self, mocked_delay
    ) -> None:
        """Registering a user stores an OTP and queues a verification email."""
        response = self.client.post(
            self.register_url,
            {
                "email": "reader@example.com",
                "password": "strongpass123",
                "first_name": "Ada",
                "last_name": "Reader",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(email="reader@example.com")
        self.assertFalse(user.is_email_verified)
        self.assertIsNotNone(get_email_verification_otp(user.email))
        mocked_delay.assert_called_once()

    def test_login_rejects_unverified_user(self) -> None:
        """Unverified users cannot log in until they confirm their email."""
        user = User.objects.create_user(
            email="reader@example.com",
            password="strongpass123",
            first_name="Ada",
        )

        response = self.client.post(
            self.login_url,
            {"email": user.email, "password": "strongpass123"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "Email is not verified.")

    def test_verify_email_marks_user_as_verified(self) -> None:
        """A correct OTP verifies the user's email and clears the stored code."""
        user = User.objects.create_user(
            email="reader@example.com",
            password="strongpass123",
        )
        set_email_verification_otp(user.email, "123456")

        response = self.client.post(
            self.verify_url,
            {"email": user.email, "otp": "123456"},
            format="json",
        )

        user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(user.is_email_verified)
        self.assertIsNone(get_email_verification_otp(user.email))

    @patch("apps.users.services.send_email.delay")
    def test_resend_verification_sends_fresh_otp(self, mocked_delay) -> None:
        """Resending verification stores a new OTP and queues another email."""
        user = User.objects.create_user(
            email="reader@example.com",
            password="strongpass123",
        )

        response = self.client.post(
            self.resend_url,
            {"email": user.email},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(get_email_verification_otp(user.email))
        mocked_delay.assert_called_once()

    def test_send_email_task_uses_django_email_backend(self) -> None:
        """The Celery email task delegates delivery to Django's mail backend."""
        result = send_email(
            "reader@example.com",
            "Verify your BookNest email",
            "Your OTP is 123456",
        )

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["reader@example.com"])
        self.assertEqual(mail.outbox[0].subject, "Verify your BookNest email")
