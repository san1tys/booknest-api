# Python modules
import os

# Project modules
from settings.conf import *
# ------------------------
# Path
# ------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_URLCONF = 'settings.urls'
WSGI_APPLICATION = 'settings.wsgi.application'
ASGI_APPLICATION = 'settings.wsgi.application'
AUTH_USER_MODEL = 'users.User'

# ------------------------
# Apps
# ------------------------
DJANGO_AND_THIRD_PARTY_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # unfold for admin dashboards
    "unfold",  
    "unfold.contrib.filters",  # optional, if special filters are needed
    "unfold.contrib.forms",  # optional, if special form elements are needed
    "unfold.contrib.inlines",  # optional, if special inlines are needed
    "unfold.contrib.import_export",  # optional, if django-import-export package is used
    "unfold.contrib.guardian",  # optional, if django-guardian package is used
    "unfold.contrib.simple_history",  # optional, if django-simple-history package is used
    "unfold.contrib.location_field",  # optional, if django-location-field package is used
    "unfold.contrib.constance",  # optional, if django-constance package is used

    
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    "django_filters",
]
PROJECT_APPS = [
    # Local apps
    "apps.users",
    "apps.hotels",
    "apps.bookings",
]
INSTALLED_APPS = DJANGO_AND_THIRD_PARTY_APPS + PROJECT_APPS
UNFOLD = {
    "SITE_HEADER":"Eatly admin panel",
    "SITE_TITLE": "Eatly dashboards",
    "SITE_SUBTITLE": "User management",
    "THEME": "dark",
    "SHOW_THEME_TOGGLE": True,
    "COLOR_PALETTE": {
        "primary":"#10b981",
        "accent": "#f97316",
        "background": "#111827",
        "foreground": "#f3f4f6",
        "muted": "#6b7280",
    }
}


# ------------------------
# Miidleware | Templates | Validators
# ------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ------------------------
# Internationalization 
# ------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC+5:00'
USE_I18N = True
USE_TZ = True

# ------------------------
# Static | Media
# ------------------------
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'