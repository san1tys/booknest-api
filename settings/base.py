# Python modules
import os

# Project modules
from settings.conf import *

# ------------------------
# Path
# ------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_URLCONF = "settings.urls"
WSGI_APPLICATION = "settings.wsgi.application"
ASGI_APPLICATION = "settings.asgi.application"
AUTH_USER_MODEL = "users.User"

# ------------------------
# Apps
# ------------------------
UNFOLD_APPS = []
try:
    import unfold  # noqa: F401
except ImportError:
    UNFOLD_APPS = []
else:
    UNFOLD_APPS = [
        # Must be before django.contrib.admin (overrides templates/static)
        "unfold",
        "unfold.contrib.filters",
        "unfold.contrib.forms",
        "unfold.contrib.inlines",
    ]

DJANGO_AND_THIRD_PARTY_APPS = [
    # Django
    *UNFOLD_APPS,
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "django_filters",
]
PROJECT_APPS = [
    # Local apps
    "apps.users",
    "apps.hotels",
    "apps.bookings",
    "apps.abstract",
]
INSTALLED_APPS = DJANGO_AND_THIRD_PARTY_APPS + PROJECT_APPS
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


# ------------------------
# Miidleware | Templates | Validators
# ------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ------------------------
# Internationalization
# ------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ------------------------
# Static | Media
# ------------------------
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
