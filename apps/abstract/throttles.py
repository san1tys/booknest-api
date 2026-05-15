import logging
from typing import Any

from rest_framework.throttling import (
    AnonRateThrottle,
    ScopedRateThrottle,
    UserRateThrottle,
)

logger = logging.getLogger(__name__)


class RedisThrottleMixin:
    """Fail open when Redis is unavailable so API traffic is not blocked."""

    def allow_request(self, request: Any, view: Any) -> bool:
        """Allow the request when Redis throttling cannot be evaluated."""
        try:
            return super().allow_request(request, view)
        except Exception as exc:
            logger.warning("Redis rate limiting unavailable: %s", exc)
            return True

    def wait(self) -> float | None:
        """Return retry wait time, or none if Redis wait calculation fails."""
        try:
            return super().wait()
        except Exception as exc:
            logger.warning("Redis throttle wait calculation failed: %s", exc)
            return None


class RedisAnonRateThrottle(RedisThrottleMixin, AnonRateThrottle):
    """Redis-backed anonymous request throttle."""

    pass


class RedisUserRateThrottle(RedisThrottleMixin, UserRateThrottle):
    """Redis-backed authenticated user request throttle."""

    pass


class RedisScopedRateThrottle(RedisThrottleMixin, ScopedRateThrottle):
    """Redis-backed scoped request throttle for sensitive endpoints."""

    pass
