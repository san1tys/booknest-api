# Project modules
from datetime import timedelta
from urllib.parse import quote

from decouple import config

# -----------------------------------
# Env id
# -----------------------------------
ENV_POSSIBLE_OPTIONS = (
    "local",
    "prod",
)
ENV_ID = config("BOOKNEST_ENV_ID", default="local", cast=str)
SECRET_KEY = config("SECRET_KEY", cast=str)

UNFOLD = {
    "SITE_HEADER": "Booknest admin panel",
    "SITE_TITLE": "Booknest dashboards",
    "SITE_SUBTITLE": "User management",
    "THEME": "dark",
    "SHOW_THEME_TOGGLE": True,
    "DASHBOARD_CALLBACK": "settings.unfold_dashboard.dashboard_callback",
    "COLOR_PALETTE": {
        "primary": "#10b981",
        "accent": "#f97316",
        "background": "#111827",
        "foreground": "#f3f4f6",
        "muted": "#6b7280",
    },
}

# ----------------------------------------------
# Redis | Cache | Temporary Data
#
REDIS_HOST = config("REDIS_HOST", default="localhost", cast=str)
REDIS_PORT = config("REDIS_PORT", default=6379, cast=int)
REDIS_DB = config("REDIS_DB", default=0, cast=int)
REDIS_CELERY_DB = config("REDIS_CELERY_DB", default=1, cast=int)
REDIS_PASSWORD = config("REDIS_PASSWORD", default="", cast=str)
REDIS_TIMEOUT_SECONDS = config("REDIS_TIMEOUT_SECONDS", default=2, cast=int)
REDIS_KEY_PREFIX = config("REDIS_KEY_PREFIX", default="booknest", cast=str)
REDIS_IGNORE_EXCEPTIONS = config(
    "REDIS_IGNORE_EXCEPTIONS",
    default=True,
    cast=bool,
)
DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS = config(
    "DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS",
    default=False,
    cast=bool,
)

_REDIS_AUTH = f":{quote(REDIS_PASSWORD, safe='')}@" if REDIS_PASSWORD else ""
REDIS_URL = config(
    "REDIS_URL",
    default=f"redis://{_REDIS_AUTH}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
    cast=str,
)

CACHE_TTL_SECONDS = config("CACHE_TTL_SECONDS", default=300, cast=int)
TEMP_DATA_TTL_SECONDS = config("TEMP_DATA_TTL_SECONDS", default=300, cast=int)
LANGUAGE_PREFERENCE_TTL_SECONDS = config(
    "LANGUAGE_PREFERENCE_TTL_SECONDS", default=60 * 60 * 24 * 30, cast=int
)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": REDIS_KEY_PREFIX,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "socket_connect_timeout": REDIS_TIMEOUT_SECONDS,
                "socket_timeout": REDIS_TIMEOUT_SECONDS,
            },
            "IGNORE_EXCEPTIONS": REDIS_IGNORE_EXCEPTIONS,
        },
    }
}

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default=REDIS_URL, cast=str)
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default=REDIS_URL, cast=str)

RATE_LIMIT_ANON = config("RATE_LIMIT_ANON", default="100/hour", cast=str)
RATE_LIMIT_USER = config("RATE_LIMIT_USER", default="1000/hour", cast=str)
RATE_LIMIT_AUTH = config("RATE_LIMIT_AUTH", default="10/minute", cast=str)

# ----------------------------------------------
# Email | OTP
#
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
    cast=str,
)
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="noreply@booknest.local",
    cast=str,
)
EMAIL_HOST = config("EMAIL_HOST", default="localhost", cast=str)
EMAIL_PORT = config("EMAIL_PORT", default=25, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="", cast=str)
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="", cast=str)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=False, cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)
EMAIL_TIMEOUT = config("EMAIL_TIMEOUT", default=10, cast=int)

EMAIL_VERIFICATION_OTP_LENGTH = config(
    "EMAIL_VERIFICATION_OTP_LENGTH",
    default=6,
    cast=int,
)
EMAIL_VERIFICATION_OTP_TTL_SECONDS = config(
    "EMAIL_VERIFICATION_OTP_TTL_SECONDS",
    default=600,
    cast=int,
)

# ----------------------------------------------
# Django REST Framework
#
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "apps.abstract.throttles.RedisAnonRateThrottle",
        "apps.abstract.throttles.RedisUserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": RATE_LIMIT_ANON,
        "user": RATE_LIMIT_USER,
        "auth": RATE_LIMIT_AUTH,
    },
    "DEFAULT_PAGINATION_CLASS": "apps.abstract.pagination.StandardPagination",
    "PAGE_SIZE": 20,
}

# ----------------------------------------------
# Simple JWT
#
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "ON_LOGIN_SUCCESS": "rest_framework_simplejwt.serializers.default_on_login_success",
    "ON_LOGIN_FAILED": "rest_framework_simplejwt.serializers.default_on_login_failed",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}

# ----------------------------------------------
# Shell plus configuration (Django extensions)
#
SHELL_PLUS_PRE_IMPORTS = [
    ("django.db", ("connection", "reset_queries", "connections")),
    ("datetime", ("datetime", "timedelta", "date")),
    ("json", ("loads", "dumps")),
]
SHELL_PLUS_MODEL_ALIASES = {
    "auths": {
        "CustomUser": "U",
    },
}
SHELL_PLUS = "ipython"
SHELL_PLUS_PRINT_SQL = True
SHELL_PLUS_PRINT_SQL_TRUNCATE = 1000

# ----------------------------------------------
# DRF Spectacular
#
SPECTACULAR_SETTINGS = {
    "TITLE": "BookNest API",
    "DESCRIPTION": "MidTerm Django Advanced — Hotel Booking API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
