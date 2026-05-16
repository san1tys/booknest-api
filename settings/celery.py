import os

from celery import Celery
from celery.schedules import crontab

from settings.conf import ENV_ID

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{ENV_ID}")


app = Celery("booknest")


app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


app.conf.beat_schedule = {
    "send-today-check-in-reminders": {
        "task": "apps.bookings.tasks.send_today_check_in_reminders",
        "schedule": crontab(minute=0, hour=8),
    },
}
