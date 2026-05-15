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
        try:
            return super().allow_request(request, view)
        except Exception as exc:
            logger.warning("Redis rate limiting unavailable: %s", exc)
            return True

    def wait(self) -> float | None:
        try:
            return super().wait()
        except Exception as exc:
            logger.warning("Redis throttle wait calculation failed: %s", exc)
            return None


class RedisAnonRateThrottle(RedisThrottleMixin, AnonRateThrottle):
    pass


class RedisUserRateThrottle(RedisThrottleMixin, UserRateThrottle):
    pass


class RedisScopedRateThrottle(RedisThrottleMixin, ScopedRateThrottle):
    pass
