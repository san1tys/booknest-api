#!/bin/sh
set -eu

APP_ENV="${1:-${BOOKNEST_ENV_ID:-local}}"
SEED_LOCAL_ON_FIRST_START="${SEED_LOCAL_ON_FIRST_START:-true}"

case "$APP_ENV" in
  local|prod)
    ;;
  *)
    echo "Unsupported environment: $APP_ENV"
    echo "Usage: ./scripts/start.sh [local|prod]"
    exit 1
    ;;
esac

export BOOKNEST_ENV_ID="$APP_ENV"

echo "Starting BookNest in $APP_ENV mode"
echo "Running migrations..."
python manage.py migrate --noinput

if [ "$APP_ENV" = "local" ] && [ "$SEED_LOCAL_ON_FIRST_START" = "true" ]; then
  SHOULD_SEED="$(python manage.py shell -c "from apps.bookings.models import Booking; from apps.hotels.models import Hotel; from apps.reviews.models import Review; from apps.rooms.models import Room; from apps.users.models import User; print('yes' if not any((User.objects.exists(), Hotel.objects.exists(), Room.objects.exists(), Booking.objects.exists(), Review.objects.exists())) else 'no')")"

  if [ "$SHOULD_SEED" = "yes" ]; then
    echo "Local database is empty. Running seed_data..."
    python manage.py seed_data
  else
    echo "Skipping seed_data because local data already exists."
  fi
fi

if [ "$APP_ENV" = "prod" ]; then
  echo "Launching Gunicorn..."
  exec gunicorn settings.wsgi:application --bind 0.0.0.0:8000
fi

echo "Launching Django development server..."
exec python manage.py runserver 0.0.0.0:8000
