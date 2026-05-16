# Project modules
from decouple import config

from settings.base import *

DEBUG = True
ALLOWED_HOSTS = []
USE_REDIS_IN_LOCAL = config("USE_REDIS_IN_LOCAL", default=False, cast=bool)

CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    },
}

if not USE_REDIS_IN_LOCAL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "booknest-local-cache",
        }
    }
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
