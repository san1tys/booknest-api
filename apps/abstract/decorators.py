from collections.abc import Callable
from functools import wraps
from typing import Any

from django.db.models import Manager, Model, QuerySet
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.serializers import Serializer
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND


def validate_serializer_data(
    serializer_class: type[Serializer],
    context: dict[str, Any] | None = None,
    many: bool = False,
) -> Callable[..., Callable[..., DRFResponse]]:
    """Validate request data before the view logic runs."""

    def decorator(func: Callable[..., DRFResponse]) -> Callable[..., DRFResponse]:
        """Wrap a view method with serializer validation logic."""

        @wraps(func)
        def wrapper(
            self,
            request: DRFRequest,
            *args: tuple[Any, ...],
            **kwargs: dict[str, Any],
        ) -> DRFResponse:
            """Instantiate, validate, and inject a serializer into the view."""
            local_context = dict(context or {})
            local_context["request"] = request

            if "pk" in kwargs:
                local_context["pk"] = kwargs["pk"]

            instance = kwargs.get("object")
            if instance is not None:
                local_context["object"] = instance

            data: Any
            if request.method in ("POST", "PUT", "PATCH"):
                data = request.data
            else:
                data = request.query_params

            serializer = serializer_class(
                instance=instance,
                data=data,
                context=local_context,
                many=many,
                partial=request.method == "PATCH",
            )
            if not serializer.is_valid():
                return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)

            kwargs["validated_data"] = serializer.validated_data.copy()
            kwargs["serializer"] = serializer
            return func(self, request, *args, **kwargs)

        return wrapper

    return decorator


def find_queryset_object_by_query_pk[T: Model](
    queryset: QuerySet[T] | Manager[T],
    entity_name: str,
) -> Callable[..., Callable[..., DRFResponse]]:
    """Find an object from a queryset by URL `pk` and pass it to the view."""

    def decorator(func: Callable[..., DRFResponse]) -> Callable[..., DRFResponse]:
        """Wrap a view method with primary-key object lookup logic."""

        @wraps(func)
        def wrapper(
            self,
            request: DRFRequest,
            *args: tuple[Any, ...],
            **kwargs: dict[str, Any],
        ) -> DRFResponse:
            """Load the target object or return a structured API error."""
            pk = kwargs.get("pk")
            assert pk is not None, "Primary key is not provided"

            try:
                pk_value = int(pk)
            except (TypeError, ValueError):
                return DRFResponse(
                    data={"id": [f"{entity_name} ID must be a number."]},
                    status=HTTP_400_BAD_REQUEST,
                )

            try:
                kwargs["object"] = queryset.get(pk=pk_value)
            except queryset.model.DoesNotExist:
                return DRFResponse(
                    data={
                        "id": [f"{entity_name} with ID {pk_value} hasn't been found."]
                    },
                    status=HTTP_404_NOT_FOUND,
                )
            except queryset.model.MultipleObjectsReturned:
                return DRFResponse(
                    data={
                        "id": [
                            f"Multiple {entity_name} objects returned for ID {pk_value}."
                        ]
                    },
                    status=HTTP_400_BAD_REQUEST,
                )

            return func(self, request, *args, **kwargs)

        return wrapper

    return decorator
