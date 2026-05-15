import os
from channels.routing import ProtocolTypeRouter, URLRouter

from django.core.asgi import get_asgi_application

from settings.conf import ENV_ID, ENV_POSSIBLE_OPTIONS

assert ENV_ID in ENV_POSSIBLE_OPTIONS, f"Invalid ENV_ID: {ENV_ID}. Must be one of {ENV_POSSIBLE_OPTIONS}."
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{ENV_ID}")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": None,  # Add WebSocket routes here when needed
    }
)