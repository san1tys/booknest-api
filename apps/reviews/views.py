from typing import Any

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_429_TOO_MANY_REQUESTS,
)
from rest_framework.viewsets import ViewSet

from apps.abstract.pagination import StandardPagination
from apps.abstract.redis_storage import (
    build_cache_key,
    cache_delete_pattern,
    cache_get,
    cache_set,
)
from apps.abstract.serializers import ErrorDetailSerializer
from apps.bookings.models import Booking, BookingStatus
from apps.reviews.models import Review
from apps.reviews.serializers import ReviewCreateSerializer, ReviewListSerializer
from apps.users.models import User


def _has_valid_booking_for_hotel(user: User, hotel_id: int) -> bool:
    """
    User can review a hotel only if they had at least one booking
    for any room of that hotel with status confirmed or completed.
    """
    valid_statuses = []
    for s in ("CONFIRMED", "COMPLETED", "confirmed", "completed"):
        valid_statuses.append(s)

    return Booking.objects.filter(
        user=user,
        room__hotel_id=hotel_id,
        status__in=(
            [BookingStatus.CONFIRMED, BookingStatus.COMPLETED]
            if hasattr(BookingStatus, "CONFIRMED")
            and hasattr(BookingStatus, "COMPLETED")
            else valid_statuses
        ),
    ).exists()


class HotelReviewViewSet(ViewSet):
    """
    ViewSet for listing/creating reviews for a given hotel.

    Wired via `apps.reviews.urls` to keep the classic path:
    `hotels/<hotel_id>/reviews/`.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            HTTP_200_OK: ReviewListSerializer(many=True),
            HTTP_429_TOO_MANY_REQUESTS: ErrorDetailSerializer,
        },
        summary="List hotel reviews",
        description="Return all reviews for a specific hotel.",
        parameters=[
            OpenApiParameter("page", int, description="Page number"),
            OpenApiParameter(
                "page_size", int, description="Results per page (max 100)"
            ),
        ],
    )
    def list(
        self, request: DRFRequest, hotel_id: int, *args: Any, **kwargs: Any
    ) -> DRFResponse:
        """Handle GET request to list reviews for a hotel.
        Args:
            request (DRFRequest): The incoming HTTP request.
            hotel_id (int): The ID of the hotel for which to list reviews.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        Returns:
            DRFResponse: The HTTP response containing the list of reviews or error information.
        """
        cache_key = build_cache_key(
            "reviews:hotel:list", hotel_id, request.get_full_path()
        )
        cached_data = cache_get(cache_key)
        if cached_data is not None:
            return DRFResponse(cached_data, status=HTTP_200_OK)

        queryset: QuerySet[Review] = (
            Review.objects.select_related("user", "hotel")
            .filter(hotel_id=hotel_id)
            .order_by("pk")
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer: ReviewListSerializer = ReviewListSerializer(page, many=True)
        response: DRFResponse = paginator.get_paginated_response(serializer.data)
        cache_set(cache_key, response.data)
        return response

    @extend_schema(
        request=ReviewCreateSerializer,
        responses={
            HTTP_201_CREATED: ReviewListSerializer,
            HTTP_400_BAD_REQUEST: dict,
            HTTP_401_UNAUTHORIZED: ErrorDetailSerializer,
            HTTP_429_TOO_MANY_REQUESTS: ErrorDetailSerializer,
        },
        summary="Create hotel review",
        description=(
            "Create a review for a hotel. Allowed only if the user had a booking "
            "for this hotel with status confirmed/completed."
        ),
    )
    def create(
        self, request: DRFRequest, hotel_id: int, *args: Any, **kwargs: Any
    ) -> DRFResponse:
        """
        Handle POST request to create a review for a hotel.
        Validations:
        - User must be authenticated.
        - User must have at least one confirmed/completed booking for the hotel.
        - User can review the hotel only once.
        args:
            request (DRFRequest): The incoming HTTP request containing review data.
            hotel_id (int): The ID of the hotel being reviewed.
        returns:
            DRFResponse: The HTTP response containing the created review data or error details.
        """
        if not IsAuthenticated().has_permission(request, self):
            return DRFResponse(
                {"detail": _("Authentication credentials were not provided.")},
                status=HTTP_401_UNAUTHORIZED,
            )

        if not _has_valid_booking_for_hotel(request.user, int(hotel_id)):
            return DRFResponse(
                {
                    "detail": _(
                        "You can review this hotel only after a confirmed/completed booking."
                    )
                },
                status=HTTP_400_BAD_REQUEST,
            )

        if Review.objects.filter(user=request.user, hotel_id=hotel_id).exists():
            return DRFResponse(
                {"detail": _("You already reviewed this hotel.")},
                status=HTTP_400_BAD_REQUEST,
            )

        serializer: ReviewCreateSerializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review: Review = Review.objects.create(
            user=request.user,
            hotel_id=hotel_id,
            **serializer.validated_data,
        )
        cache_delete_pattern("reviews:hotel:list:*")

        return DRFResponse(ReviewListSerializer(review).data, status=HTTP_201_CREATED)
