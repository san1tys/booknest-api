#!/bin/sh
set -eu

APP_ENV="${1:-local}"
ACTION="${2:-up}"
shift $(( $# >= 1 ? 1 : 0 ))
shift $(( $# >= 1 ? 1 : 0 ))

case "$APP_ENV" in
  local|prod)
    ;;
  *)
    echo "Unsupported environment: $APP_ENV"
    echo "Usage: ./scripts/build.sh [local|prod] [build|up] [extra docker compose args...]"
    exit 1
    ;;
esac

case "$ACTION" in
  build|up)
    ;;
  *)
    echo "Unsupported action: $ACTION"
    echo "Usage: ./scripts/build.sh [local|prod] [build|up] [extra docker compose args...]"
    exit 1
    ;;
esac

export BOOKNEST_ENV_ID="$APP_ENV"
export COMPOSE_PROFILES="$APP_ENV"

if [ "$ACTION" = "build" ]; then
  echo "Building Docker image for $APP_ENV..."
  exec docker compose build "$@" web
fi

echo "Building and starting Docker services for $APP_ENV..."
exec docker compose up --build "$@"
