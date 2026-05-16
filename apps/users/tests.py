from unittest.mock import MagicMock, patch

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.abstract.testing import bearer_token, build_locmem_caches
from apps.users.models import User
from apps.users.services import (
    get_email_verification_otp,
    set_email_verification_otp,
)
from apps.users.tasks import send_otp as send_email

LOC_MEM_CACHES = build_locmem_caches("users-otp-tests")


USER_ENDPOINT_CACHES = build_locmem_caches("users-endpoint-tests")


@override_settings(
    CACHES=LOC_MEM_CACHES,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    LANGUAGE_CODE="en",
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
        self, mocked_delay: MagicMock
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
    def test_resend_verification_sends_fresh_otp(
        self, mocked_delay: MagicMock
    ) -> None:
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


@override_settings(
    CACHES=USER_ENDPOINT_CACHES,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class UserEndpointTests(TestCase):
    """Endpoint tests for the user viewset (me, register, verify, resend, login, language)."""

    def setUp(self) -> None:
        """Build a verified and unverified user plus authed/anonymous clients."""
        cache.clear()
        self.password = "strongpass123"
        self.verified_user = User.objects.create_user(
            email="verified@example.com",
            password=self.password,
            first_name="Ada",
            last_name="Reader",
            is_email_verified=True,
        )
        self.unverified_user = User.objects.create_user(
            email="unverified@example.com",
            password=self.password,
            first_name="Unverified",
        )

        self.client = APIClient()
        self.auth_client = APIClient()
        self.auth_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {bearer_token(self.verified_user)}"
        )

        self.me_url = "/api/users/v1/users/me"
        self.register_url = "/api/users/v1/users/register"
        self.verify_url = "/api/users/v1/users/verify-email"
        self.resend_url = "/api/users/v1/users/resend-verification"
        self.login_url = "/api/users/v1/users/login"
        self.language_url = "/api/users/v1/users/language"

    # --- GET /me -------------------------------------------------------------

    def test_me_returns_200_with_user_data(self) -> None:
        """Authenticated user receives their profile data."""
        response = self.auth_client.get(self.me_url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["email"], self.verified_user.email)
        self.assertTrue(response.data["is_email_verified"])

    def test_me_returns_401_for_anonymous(self) -> None:
        """Anonymous request to /me is rejected."""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 401)

    def test_me_does_not_leak_password_hash(self) -> None:
        """The /me response must not expose the password field."""
        response = self.auth_client.get(self.me_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.data)

    # --- POST /register ------------------------------------------------------

    @patch("apps.users.services.send_email.delay")
    def test_register_creates_unverified_user(self, mocked_delay: MagicMock) -> None:
        """Valid registration creates a new unverified user and queues an OTP email."""
        response = self.client.post(
            self.register_url,
            {
                "email": "newcomer@example.com",
                "password": self.password,
                "first_name": "New",
                "last_name": "Comer",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(email="newcomer@example.com")
        self.assertFalse(user.is_email_verified)
        mocked_delay.assert_called_once()

    def test_register_returns_400_when_email_missing(self) -> None:
        """Registration without an email returns a 400 validation error."""
        response = self.client.post(
            self.register_url,
            {"password": self.password, "first_name": "NoEmail"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data)

    def test_register_returns_400_when_password_too_short(self) -> None:
        """Password shorter than six characters is rejected."""
        response = self.client.post(
            self.register_url,
            {"email": "shortpw@example.com", "password": "abc"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.data)

    # --- POST /verify-email --------------------------------------------------

    def test_verify_email_returns_200_with_valid_otp(self) -> None:
        """A correct OTP marks the user as verified."""
        set_email_verification_otp(self.unverified_user.email, "654321")
        response = self.client.post(
            self.verify_url,
            {"email": self.unverified_user.email, "otp": "654321"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.unverified_user.refresh_from_db()
        self.assertTrue(self.unverified_user.is_email_verified)

    def test_verify_email_returns_400_for_invalid_otp(self) -> None:
        """A wrong OTP yields a 400 response."""
        set_email_verification_otp(self.unverified_user.email, "111111")
        response = self.client.post(
            self.verify_url,
            {"email": self.unverified_user.email, "otp": "999999"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_verify_email_returns_404_for_unknown_email(self) -> None:
        """An unknown email returns 404."""
        response = self.client.post(
            self.verify_url,
            {"email": "missing@example.com", "otp": "123456"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    # --- POST /resend-verification -------------------------------------------

    @patch("apps.users.services.send_email.delay")
    def test_resend_verification_returns_200(self, mocked_delay: MagicMock) -> None:
        """Unverified users can request a fresh OTP."""
        response = self.client.post(
            self.resend_url,
            {"email": self.unverified_user.email},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        mocked_delay.assert_called_once()

    def test_resend_verification_returns_400_for_already_verified(self) -> None:
        """Already-verified users get a 400 response."""
        response = self.client.post(
            self.resend_url,
            {"email": self.verified_user.email},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_resend_verification_returns_404_for_unknown_email(self) -> None:
        """Unknown emails yield 404."""
        response = self.client.post(
            self.resend_url,
            {"email": "ghost@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    # --- POST /login ---------------------------------------------------------

    def test_login_returns_tokens_for_verified_user(self) -> None:
        """A verified user can log in and receive JWT tokens."""
        response = self.client.post(
            self.login_url,
            {"email": self.verified_user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_returns_401_for_wrong_password(self) -> None:
        """Invalid password is rejected with 401."""
        response = self.client.post(
            self.login_url,
            {"email": self.verified_user.email, "password": "wrong-pass"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_login_returns_401_for_unverified_user(self) -> None:
        """Unverified users cannot log in even with the right password."""
        response = self.client.post(
            self.login_url,
            {"email": self.unverified_user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    # --- POST /language ------------------------------------------------------

    def test_language_set_returns_200_for_valid_choice(self) -> None:
        """A valid language is accepted and echoed back."""
        response = self.auth_client.post(
            self.language_url, {"language": "en"}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["language"], "en")

    def test_language_returns_401_for_anonymous(self) -> None:
        """Anonymous users cannot set language preference."""
        response = self.client.post(
            self.language_url, {"language": "en"}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_language_returns_400_for_invalid_choice(self) -> None:
        """An unsupported language is rejected with 400."""
        response = self.auth_client.post(
            self.language_url, {"language": "fr"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    # --- POST /logout --------------------------------------------------------

    def test_logout_blacklists_token(self) -> None:
        """Logging out blacklists the refresh token so it cannot be reused."""
        login_response = self.client.post(
            self.login_url,
            {"email": self.verified_user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200, login_response.data)
        refresh_token = login_response.data["refresh"]
        access_token = login_response.data["access"]

        logout_client = APIClient()
        logout_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        logout_response = logout_client.post(
            "/api/users/v1/users/logout",
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(logout_response.status_code, 200, logout_response.data)

        refresh_response = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, 401)

    def test_logout_without_token(self) -> None:
        """POSTing logout without a refresh token returns 400."""
        response = self.auth_client.post(
            "/api/users/v1/users/logout", {}, format="json"
        )
        self.assertEqual(response.status_code, 400)
