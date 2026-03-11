from datetime import date
from typing import Any

from django.db.models import Q, QuerySet
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from rest_framework.viewsets import ViewSet

from apps.abstract.serializers import ErrorDetailSerializer, ValidationErrorSerializer
from apps.bookings.models import Booking, BookingStatus
from apps.bookings.serializers import (
    AvailabilityQuerySerializer,
    AvailabilityResponseSerializer,
    BookingCancelSerializer,
    BookingCreateSerializer,
    BookingListSerializer,
)
from apps.users.models import User


class BookingViewSet(ViewSet):
    """ViewSet for managing bookings"""

    permission_classes = [IsAuthenticated]
    serializer_class = BookingListSerializer
    queryset = Booking.objects.all()

    def get_serializer_class(self):
        """Return serializer class based on current action"""
        if self.action == "create_booking":
            return BookingCreateSerializer
        if self.action == "list_bookings":
            return BookingListSerializer
        if self.action == "check_availability":
            return AvailabilityResponseSerializer
        if self.action == "cancel_booking":
            return BookingCancelSerializer
        return self.serializer_class

    @extend_schema(
        request=BookingCreateSerializer,
        responses={
            HTTP_201_CREATED: BookingListSerializer,
            HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            HTTP_403_FORBIDDEN: ErrorDetailSerializer,
        },
        description="Create a new booking for a room. The user must be authenticated. The request should include the room ID, check-in date, and check-out date. The response will include the details of the created booking.",
        summary="Create a new booking",
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="create",
        url_name="create",
        permission_classes=[IsAuthenticated],
    )
    def create_booking(
        self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]
    ) -> DRFResponse:
        """
        Handle POST request to create a new booking.

        Args:
            request (DRFRequest): The incoming HTTP request containing booking data.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.

        Returns:
            DRFResponse: The HTTP response containing the created booking details or error information.
        """

        serializer: BookingCreateSerializer = BookingCreateSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            booking = serializer.save()
            return DRFResponse(
                BookingListSerializer(booking).data, status=HTTP_201_CREATED
            )

        return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={
            HTTP_200_OK: BookingListSerializer(many=True),
        },
        description="List all bookings for the authenticated user. The user must be authenticated to access this endpoint. The response will include a list of bookings with details such as room information, check-in and check-out dates, status, and total price.",
        summary="List user bookings",
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="list",
        url_name="list",
        permission_classes=[IsAuthenticated],
    )
    def list_bookings(
        self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]
    ) -> DRFResponse:
        """
        Handle GET request to list all bookings for the authenticated user.

        Args:
            request (DRFRequest): The incoming HTTP request from the authenticated user.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.

        Returns:
            DRFResponse: The HTTP response containing a list of bookings or error information.
        """

        queryset: QuerySet[Booking] = Booking.objects.select_related(
            "user", "room", "room__hotel", "room__hotel__owner"
        ).order_by("-created_at")

        user: User = request.user

        if user.hotels.exists():
            queryset = queryset.filter(room__hotel__owner=user)
        else:
            queryset = queryset.filter(user=user)

        serializer = BookingListSerializer(queryset, many=True)
        return DRFResponse(serializer.data, status=HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="room",
                description="ID of the room to check availability for",
                required=True,
                type=int,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="check_in",
                description="Check-in date in YYYY-MM-DD format",
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="check_out",
                description="Check-out date in YYYY-MM-DD format",
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={
            HTTP_200_OK: AvailabilityResponseSerializer,
            HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
        },
        description="Check the availability of a room for specific check-in and check-out dates. The user must provide the room ID, check-in date, and check-out date as query parameters. The response will indicate whether the room is available for the specified dates.",
        summary="Check room availability",
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="availability",
        url_name="availability",
        permission_classes=[IsAuthenticated],
    )
    def check_availability(
        self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]
    ) -> DRFResponse:
        """
        Handle GET request to check the availability of a room for specific dates.

        Args:
            request (DRFRequest): The incoming HTTP request containing query parameters for room availability.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.

        Returns:
            DRFResponse: The HTTP response indicating room availability or error information.
        """
        serializer: AvailabilityQuerySerializer = AvailabilityQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)

        room: int = serializer.validated_data["room"]
        check_in: date = serializer.validated_data["check_in"]
        check_out: date = serializer.validated_data["check_out"]

        overlapping_bookings: QuerySet[Booking] = Booking.objects.filter(
            room_id=room,
            status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
        ).filter(Q(check_in__lt=check_out) & Q(check_out__gt=check_in))

        response_data: dict[str, Any] = {
            "room": room,
            "check_in": check_in,
            "check_out": check_out,
            "available": not overlapping_bookings.exists(),
        }

        response_serializer: AvailabilityResponseSerializer = AvailabilityResponseSerializer(instance=response_data)
        return DRFResponse(response_serializer.data, status=HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="pk",
                type=int,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID of the booking to cancel",
            )
        ],
        responses={
            HTTP_200_OK: BookingCancelSerializer,
            HTTP_403_FORBIDDEN: ErrorDetailSerializer,
            HTTP_404_NOT_FOUND: ErrorDetailSerializer,
        },
        description="Cancel a booking by its ID. The user must be authenticated and either the owner of the booking or the owner of the hotel associated with the booking to cancel it. The response will include the details of the cancelled booking.",
        summary="Cancel a booking",
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="cancel",
        url_name="cancel",
        permission_classes=[IsAuthenticated],
    )
    def cancel_booking(
        self,
        request: DRFRequest,
        pk: int = None,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """
        Handle POST request to cancel a booking by its ID.

        Args:
            request (DRFRequest): The incoming HTTP request from the authenticated user.
            pk (int): The primary key of the booking to be cancelled.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.

        Returns:
            DRFResponse: The HTTP response containing the details of the cancelled booking or error information.
        """
        try:
            booking: Booking = Booking.objects.select_related(
                "user", "room", "room__hotel", "room__hotel__owner"
            ).get(pk=pk)
        except Booking.DoesNotExist:
            return DRFResponse(
                {"detail": "Booking not found"}, status=HTTP_404_NOT_FOUND
            )

        is_booking_owner: bool = booking.user == request.user
        is_hotel_owner: bool = booking.room.hotel.owner == request.user

        if not (is_booking_owner or is_hotel_owner):
            return DRFResponse(
                {"detail": "You do not have permission to cancel this booking."},
                status=HTTP_403_FORBIDDEN,
            )

        if booking.status == BookingStatus.CANCELLED:
            return DRFResponse(
                {"detail": "This booking is already cancelled."},
                status=HTTP_400_BAD_REQUEST,
            )

        booking.status = BookingStatus.CANCELLED
        booking.save()

        serializer: BookingCancelSerializer = BookingCancelSerializer(booking)
        return DRFResponse(serializer.data, status=HTTP_200_OK)
