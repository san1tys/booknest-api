import json
from typing import Any
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


class BookingStatusConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer that streams booking status updates to a single user."""

    GROUP_PREFIX = "bookings_"

    @classmethod
    def _group_name(cls, user_id: int | str) -> str:
        return f"{cls.GROUP_PREFIX}{user_id}"

    async def connect(self) -> None:
        token = self._extract_token(self.scope.get("query_string", b""))
        if token is None:
            await self.close(code=4401)
            return

        try:
            validated = AccessToken(token)
        except TokenError:
            await self.close(code=4401)
            return

        user_id = validated.get("user_id")
        if user_id is None:
            await self.close(code=4401)
            return

        self.user_id = user_id
        self.group_name = self._group_name(user_id)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code: int) -> None:
        group_name = getattr(self, "group_name", None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        if not text_data:
            return
        try:
            payload = json.loads(text_data)
        except (TypeError, ValueError):
            return
        if isinstance(payload, dict) and payload.get("type") == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))

    async def booking_status(self, event: dict[str, Any]) -> None:
        await self.send(
            text_data=json.dumps(
                {
                    "type": "booking_status",
                    "booking_id": event["booking_id"],
                    "status": event["status"],
                }
            )
        )

    @classmethod
    async def notify(cls, user_id: int, booking_id: int, status: str) -> None:
        """Push a booking status update to the user's group."""
        layer = get_channel_layer()
        await layer.group_send(
            cls._group_name(user_id),
            {
                "type": "booking_status",
                "booking_id": booking_id,
                "status": status,
            },
        )

    @staticmethod
    def _extract_token(query_string: bytes) -> str | None:
        try:
            decoded = query_string.decode("utf-8")
        except UnicodeDecodeError:
            return None
        params = parse_qs(decoded)
        tokens = params.get("token") or []
        return tokens[0] if tokens else None
