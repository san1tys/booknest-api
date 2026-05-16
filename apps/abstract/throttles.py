import logging

from rest_framework.throttling import (
    AnonRateThrottle,
    ScopedRateThrottle,
    UserRateThrottle,
)

from apps.abstract.mixins import RedisThrottleMixin

logger = logging.getLogger(__name__)


class RedisAnonRateThrottle(RedisThrottleMixin, AnonRateThrottle):
    """Redis-backed anonymous request throttle."""

    pass


class RedisUserRateThrottle(RedisThrottleMixin, UserRateThrottle):
    """Redis-backed authenticated user request throttle."""

    pass


class RedisScopedRateThrottle(RedisThrottleMixin, ScopedRateThrottle):
    """Redis-backed scoped request throttle for sensitive endpoints."""

    pass
