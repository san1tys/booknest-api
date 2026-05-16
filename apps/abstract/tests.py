import time

from asgiref.sync import async_to_sync
from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings
from rest_framework_simplejwt.tokens import AccessToken

from apps.abstract.async_io import AsyncOperationTimeout, run_sync_io
from apps.abstract.middleware import (
    RedisLanguagePreferenceMiddleware,
    normalize_language,
)
from apps.abstract.redis_storage import (
    delete_temporary_data,
    get_language_preference,
    get_temporary_data,
    request_cache_identifier,
    set_temporary_data,
)

LOC_MEM_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "redis-tests",
    }
}


@override_settings(CACHES=LOC_MEM_CACHES)
class RedisStorageTests(SimpleTestCase):
    """Tests for Redis-backed temporary data and language preference helpers."""

    def setUp(self) -> None:
        """Clear the in-memory test cache before each test."""
        cache.clear()

    def test_temporary_data_helpers_store_and_delete_refresh_token(self) -> None:
        """Temporary helpers store refresh-token metadata used by login."""
        refresh_token_data = {"user_id": 1, "email": "user@example.com"}

        set_temporary_data(
            "refresh_token",
            "token-jti",
            refresh_token_data,
            timeout=60,
        )

        self.assertEqual(
            get_temporary_data("refresh_token", "token-jti"),
            refresh_token_data,
        )

        delete_temporary_data("refresh_token", "token-jti")
        self.assertIsNone(get_temporary_data("refresh_token", "token-jti"))

    @override_settings(LANGUAGES=(("en-us", "English"), ("ru", "Russian")))
    def test_language_preference_middleware_stores_supported_language(self) -> None:
        """Language middleware stores a supported request language in cache."""
        factory = RequestFactory()
        request = factory.get("/", HTTP_X_LANGUAGE="ru", REMOTE_ADDR="127.0.0.1")
        middleware = RedisLanguagePreferenceMiddleware(lambda req: HttpResponse("ok"))

        response = middleware(request)

        self.assertEqual(request.LANGUAGE_CODE, "ru")
        self.assertEqual(response.headers["Content-Language"], "ru")
        self.assertEqual(
            get_language_preference(request_cache_identifier(request)),
            "ru",
        )

    @override_settings(LANGUAGES=(("en-us", "English"), ("kk", "Kazakh")))
    def test_language_preference_middleware_uses_jwt_user_key(self) -> None:
        """Language middleware stores authenticated preferences by JWT user id."""
        token = AccessToken()
        token["user_id"] = 7
        factory = RequestFactory()
        request = factory.get(
            "/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_LANGUAGE="kk",
            REMOTE_ADDR="127.0.0.1",
        )
        middleware = RedisLanguagePreferenceMiddleware(lambda req: HttpResponse("ok"))

        middleware(request)

        self.assertEqual(get_language_preference("user:7"), "kk")

    @override_settings(LANGUAGES=(("en-us", "English"), ("ru", "Russian")))
    def test_normalize_language_accepts_base_language_matches(self) -> None:
        """Language normalization maps regional values to supported languages."""
        self.assertEqual(normalize_language("en-US,en;q=0.9"), "en-us")
        self.assertEqual(normalize_language("ru-RU"), "ru")
        self.assertIsNone(normalize_language("fr"))


class AsyncIoTests(SimpleTestCase):
    """Tests for shared async I/O helpers."""

    def test_run_sync_io_executes_blocking_callable(self) -> None:
        """Blocking I/O callables run through the async wrapper."""
        result = async_to_sync(run_sync_io)(
            "test_blocking_operation",
            lambda: "finished",
            timeout=1,
        )

        self.assertEqual(result, "finished")

    def test_run_sync_io_raises_timeout(self) -> None:
        """Slow I/O operations fail with a timeout-specific exception."""

        def slow_operation() -> str:
            time.sleep(0.05)
            return "too late"

        with self.assertRaises(AsyncOperationTimeout):
            async_to_sync(run_sync_io)(
                "slow_blocking_operation",
                slow_operation,
                timeout=0.001,
            )
