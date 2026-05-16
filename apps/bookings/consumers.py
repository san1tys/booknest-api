import asyncio
import json
import logging
from typing import Any
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)


class BookingStatusConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer that streams booking status updates to a single user."""

    GROUP_PREFIX = "bookings_"

    @classmethod
    def _group_name(cls, user_id: int | str) -> str:
        return f"{cls.GROUP_PREFIX}{user_id}"

    async def connect(self) -> None:
        token = self._extract_token(self.scope.get("query_string", b""))
        if token is None:
            logger.warning("Rejected booking websocket connection without token")
            await self.close(code=4401)
            return

        try:
            validated = AccessToken(token)
        except TokenError:
            logger.warning("Rejected booking websocket connection with invalid token")
            await self.close(code=4401)
            return

        user_id = validated.get("user_id")
        if user_id is None:
            logger.warning(
                "Rejected booking websocket connection without user_id claim"
            )
            await self.close(code=4401)
            return

        self.user_id = user_id
        self.group_name = self._group_name(user_id)

        try:
            await asyncio.wait_for(
                self.channel_layer.group_add(self.group_name, self.channel_name),
                timeout=settings.ASYNC_IO_TIMEOUT_SECONDS,
            )
        except TimeoutError:
            logger.exception(
                "Timed out joining booking websocket group %s", self.group_name
            )
            await self.close(code=1011)
            return
        except Exception:
            logger.exception(
                "Failed to join booking websocket group %s", self.group_name
            )
            await self.close(code=1011)
            return

        await self.accept()
        logger.info("Accepted booking websocket for user %s", user_id)

    async def disconnect(self, code: int) -> None:
        group_name = getattr(self, "group_name", None)
        if group_name:
            try:
                await asyncio.wait_for(
                    self.channel_layer.group_discard(group_name, self.channel_name),
                    timeout=settings.ASYNC_IO_TIMEOUT_SECONDS,
                )
            except TimeoutError:
                logger.exception(
                    "Timed out leaving booking websocket group %s", group_name
                )
            except Exception:
                logger.exception(
                    "Failed to leave booking websocket group %s", group_name
                )
            else:
                logger.info("Disconnected booking websocket from group %s", group_name)

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        if not text_data:
            return
        try:
            payload = json.loads(text_data)
        except (TypeError, ValueError):
            logger.warning("Ignored malformed booking websocket payload")
            return
        if isinstance(payload, dict) and payload.get("type") == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))

    async def booking_status(self, event: dict[str, Any]) -> None:
        logger.info(
            "Sending booking status websocket event for booking %s",
            event["booking_id"],
        )
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
    async def notify(cls, user_id: int, booking_id: int, status: str) -> bool:
        """Push a booking status update to the user's group."""
        layer = get_channel_layer()
        if layer is None:
            logger.error(
                "Cannot send booking status notification without channel layer"
            )
            return False

        group_name = cls._group_name(user_id)
        try:
            await asyncio.wait_for(
                layer.group_send(
                    group_name,
                    {
                        "type": "booking_status",
                        "booking_id": booking_id,
                        "status": status,
                    },
                ),
                timeout=settings.ASYNC_IO_TIMEOUT_SECONDS,
            )
        except TimeoutError:
            logger.exception(
                "Timed out sending booking status notification to group %s",
                group_name,
            )
            return False
        except Exception:
            logger.exception(
                "Failed to send booking status notification to group %s",
                group_name,
            )
            return False

        logger.info(
            "Sent booking status notification for booking %s to group %s",
            booking_id,
            group_name,
        )
        return True

    @staticmethod
    def _extract_token(query_string: bytes) -> str | None:
        try:
            decoded = query_string.decode("utf-8")
        except UnicodeDecodeError:
            return None
        params = parse_qs(decoded)
        tokens = params.get("token") or []
        return tokens[0] if tokens else None
