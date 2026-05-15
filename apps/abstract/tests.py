from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings
from rest_framework_simplejwt.tokens import AccessToken

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
    def setUp(self) -> None:
        cache.clear()

    def test_temporary_data_helpers_store_and_delete_values(self) -> None:
        set_temporary_data("otp", "user:1", "123456", timeout=60)

        self.assertEqual(get_temporary_data("otp", "user:1"), "123456")

        delete_temporary_data("otp", "user:1")
        self.assertIsNone(get_temporary_data("otp", "user:1"))

    @override_settings(LANGUAGES=(("en-us", "English"), ("ru", "Russian")))
    def test_language_preference_middleware_stores_supported_language(self) -> None:
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
        self.assertEqual(normalize_language("en-US,en;q=0.9"), "en-us")
        self.assertEqual(normalize_language("ru-RU"), "ru")
        self.assertIsNone(normalize_language("fr"))
