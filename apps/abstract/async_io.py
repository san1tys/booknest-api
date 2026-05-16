import asyncio
import logging
from collections.abc import Callable
from typing import Any

import httpx
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class AsyncOperationError(Exception):
    """Base exception for failed async I/O operations."""


class AsyncOperationTimeout(AsyncOperationError):
    """Raised when an async I/O operation exceeds its timeout."""


def get_async_io_timeout() -> float:
    """Return the default timeout for async I/O helpers."""
    return float(getattr(settings, "ASYNC_IO_TIMEOUT_SECONDS", 10))


async def run_sync_io(
    operation_name: str,
    func: Callable[..., Any],
    *args: Any,
    timeout: float | None = None,
    **kwargs: Any,
) -> Any:
    """Run blocking I/O in a worker thread with logging and timeout handling."""
    effective_timeout = get_async_io_timeout() if timeout is None else timeout
    logger.info(
        "Starting async I/O operation '%s' with timeout %.2fs",
        operation_name,
        effective_timeout,
    )
    try:
        result = await asyncio.wait_for(
            sync_to_async(func, thread_sensitive=False)(*args, **kwargs),
            timeout=effective_timeout,
        )
    except TimeoutError as exc:
        logger.exception(
            "Async I/O operation '%s' timed out after %.2fs",
            operation_name,
            effective_timeout,
        )
        raise AsyncOperationTimeout(operation_name) from exc
    except Exception as exc:
        logger.exception("Async I/O operation '%s' failed", operation_name)
        raise AsyncOperationError(operation_name) from exc

    logger.info("Finished async I/O operation '%s'", operation_name)
    return result


async def send_mail_async(
    *,
    subject: str,
    message: str,
    from_email: str,
    recipient_list: list[str],
    timeout: float | None = None,
    operation_name: str = "send_mail",
) -> int:
    """Send email through Django's backend without blocking the event loop."""
    return await run_sync_io(
        operation_name,
        send_mail,
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=False,
        timeout=timeout,
    )


async def fetch_json_async(
    url: str,
    *,
    timeout: float | None = None,
    operation_name: str = "fetch_json",
    **request_kwargs: Any,
) -> Any:
    """Fetch JSON from an external HTTP API with httpx.AsyncClient."""
    effective_timeout = get_async_io_timeout() if timeout is None else timeout
    logger.info(
        "Starting async HTTP operation '%s' for %s with timeout %.2fs",
        operation_name,
        url,
        effective_timeout,
    )
    try:
        async with httpx.AsyncClient(timeout=effective_timeout) as client:
            response = await client.get(url, **request_kwargs)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException as exc:
        logger.exception(
            "Async HTTP operation '%s' timed out for %s after %.2fs",
            operation_name,
            url,
            effective_timeout,
        )
        raise AsyncOperationTimeout(operation_name) from exc
    except (httpx.HTTPError, ValueError) as exc:
        logger.exception("Async HTTP operation '%s' failed for %s", operation_name, url)
        raise AsyncOperationError(operation_name) from exc

    logger.info("Finished async HTTP operation '%s' for %s", operation_name, url)
    return data
