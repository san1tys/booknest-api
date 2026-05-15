from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils import translation
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken

from apps.abstract.redis_storage import (
    get_language_preference,
    request_cache_identifier,
    set_language_preference,
)


class RedisLanguagePreferenceMiddleware:
    """
    Store an explicit language selection in Redis and reuse it on later requests.

    Clients can send `X-Language`, `?lang=`, or `?language=`. The value is kept
    per authenticated user, session, or IP fallback for temporary anonymous data.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        identifier = self._language_identifier(request)
        language = self._selected_language(request)

        if language:
            set_language_preference(identifier, language)
        else:
            language = normalize_language(get_language_preference(identifier))

        activated = False
        if language:
            request.language_preference = language
            translation.activate(language)
            request.LANGUAGE_CODE = language
            activated = True

        try:
            response = self.get_response(request)
        finally:
            if activated:
                translation.deactivate()

        if language:
            response.headers["Content-Language"] = language

        return response

    def _selected_language(self, request: HttpRequest) -> str | None:
        language = (
            request.headers.get("X-Language")
            or request.GET.get("lang")
            or request.GET.get("language")
        )
        return normalize_language(language)

    def _language_identifier(self, request: HttpRequest) -> str:
        auth_header = request.headers.get("Authorization", "")
        auth_parts = auth_header.split()
        if len(auth_parts) == 2 and auth_parts[0].lower() == "bearer":
            try:
                token = UntypedToken(auth_parts[1])
                user_id_claim = settings.SIMPLE_JWT["USER_ID_CLAIM"]
                user_id = token.get(user_id_claim)
            except (InvalidToken, TokenError, KeyError):
                user_id = None

            if user_id is not None:
                return f"user:{user_id}"

        return request_cache_identifier(request)


def normalize_language(language: str | None) -> str | None:
    if not language:
        return None

    language = language.split(",")[0].strip().lower().replace("_", "-")
    supported_languages = {code.lower(): code for code, _name in settings.LANGUAGES}

    if language in supported_languages:
        return supported_languages[language]

    base_language = language.split("-")[0]
    for supported_language in supported_languages:
        if supported_language.split("-")[0] == base_language:
            return supported_languages[supported_language]

    return None
