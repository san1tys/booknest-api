import hashlib
import logging
from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest

logger = logging.getLogger(__name__)


def build_cache_key(namespace: str, *parts: Any) -> str:
    """Build a stable cache key for arbitrary request data."""
    raw_key = ":".join(str(part) for part in parts if part is not None)
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return f"{namespace}:{digest}"


def _safe_cache_call(
    operation: str,
    callback: Callable[[], Any],
    default: Any = None,
) -> Any:
    try:
        return callback()
    except Exception as exc:
        logger.warning("Redis %s failed: %s", operation, exc)
        return default


def cache_get(key: str, default: Any = None) -> Any:
    return _safe_cache_call("get", lambda: cache.get(key, default), default)


def cache_set(key: str, value: Any, timeout: int | None = None) -> bool:
    ttl = timeout if timeout is not None else settings.CACHE_TTL_SECONDS
    return bool(_safe_cache_call("set", lambda: cache.set(key, value, ttl), False))


def cache_delete(key: str) -> bool:
    return bool(_safe_cache_call("delete", lambda: cache.delete(key), False))


def cache_delete_pattern(pattern: str) -> int:
    def _delete_pattern() -> int:
        delete_pattern = getattr(cache, "delete_pattern", None)
        if delete_pattern is None:
            return 0
        return delete_pattern(pattern)

    return int(_safe_cache_call("delete_pattern", _delete_pattern, 0))


def request_cache_identifier(request: HttpRequest) -> str:
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return f"user:{user.pk}"

    session = getattr(request, "session", None)
    if session is not None and session.session_key:
        return f"session:{session.session_key}"

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    remote_addr = forwarded_for.split(",")[0].strip() if forwarded_for else ""
    return f"ip:{remote_addr or request.META.get('REMOTE_ADDR', 'unknown')}"


def temporary_data_key(name: str, identifier: str) -> str:
    return build_cache_key("temporary", name, identifier)


def set_temporary_data(
    name: str,
    identifier: str,
    value: Any,
    timeout: int | None = None,
) -> bool:
    ttl = timeout if timeout is not None else settings.TEMP_DATA_TTL_SECONDS
    return cache_set(temporary_data_key(name, identifier), value, ttl)


def get_temporary_data(name: str, identifier: str, default: Any = None) -> Any:
    return cache_get(temporary_data_key(name, identifier), default)


def delete_temporary_data(name: str, identifier: str) -> bool:
    return cache_delete(temporary_data_key(name, identifier))


def language_preference_key(identifier: str) -> str:
    return build_cache_key("language", identifier)


def set_language_preference(identifier: str, language: str) -> bool:
    return cache_set(
        language_preference_key(identifier),
        language,
        settings.LANGUAGE_PREFERENCE_TTL_SECONDS,
    )


def get_language_preference(identifier: str) -> str | None:
    return cache_get(language_preference_key(identifier))
