from typing import Any

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from rest_framework.viewsets import ViewSet

from apps.abstract.permissions import IsOwner
from apps.abstract.serializers import (
    ErrorDetailSerializer,
    MessageSerializer,
    ValidationErrorSerializer,
)
from apps.hotels.models import Hotel
from apps.rooms.models import Room
from apps.rooms.serializers import RoomCreateUpdateSerializer, RoomDetailSerializer


class RoomViewSet(ViewSet):
    """ViewSet for managing rooms."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=RoomCreateUpdateSerializer,
        responses={
            HTTP_201_CREATED: RoomDetailSerializer,
            HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            HTTP_403_FORBIDDEN: ErrorDetailSerializer,
        },
        description="Create a new room (only hotel owner). Requires auth.",
        summary="Create Room",
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="create",
        url_name="create",
        permission_classes=[IsAuthenticated],
    )
    def create_room(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """
        Handle POST request to create a new room. Only the hotel owner can create rooms.
        args:
            request (DRFRequest): The incoming request containing room data.
        returns:
            DRFResponse: The response containing the created room details or error messages.
        
        """
        serializer: RoomCreateUpdateSerializer = RoomCreateUpdateSerializer(
            data=request.data
        )
        if not serializer.is_valid():
            return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)

        hotel: Hotel = serializer.validated_data["hotel"]
        if not hotel.owner_id or hotel.owner_id != request.user.id:
            return DRFResponse(
                {"detail": "Only the hotel owner can create rooms."},
                status=HTTP_403_FORBIDDEN,
            )

        room: Room = serializer.save()
        return DRFResponse(RoomDetailSerializer(room).data, status=HTTP_201_CREATED)

    @extend_schema(
        request=RoomCreateUpdateSerializer,
        responses={
            HTTP_200_OK: RoomDetailSerializer,
            HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            HTTP_403_FORBIDDEN: ErrorDetailSerializer,
            HTTP_404_NOT_FOUND: ErrorDetailSerializer,
        },
        description="Update a room (only hotel owner). Requires auth.",
        summary="Update Room",
        parameters=[
            OpenApiParameter(
                name="id",
                description="The primary key of the room to update.",
                required=True,
                location=OpenApiParameter.PATH,
                type=int,
            )
        ],
    )
    @action(
        detail=True,
        methods=["put"],
        url_path="update",
        url_name="update",
        permission_classes=[IsOwner],
    )
    def update_room(
        self,
        request: DRFRequest,
        pk: int,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """
        Handle PUT request to update an existing room. Only the hotel owner can update rooms.
        args:
            request (DRFRequest): The incoming request containing updated room data.
            pk (int): The primary key of the room to update.
        returns:
            DRFResponse: The response containing the updated room details or error messages.
        """
        try:
            room: Room = Room.objects.select_related("hotel", "hotel__owner").get(pk=pk)
        except Room.DoesNotExist:
            return DRFResponse({"detail": "Room not found."}, status=HTTP_404_NOT_FOUND)

        if room.hotel.owner_id != request.user.id:
            return DRFResponse(
                {"detail": "You do not have permission to edit this room."},
                status=HTTP_403_FORBIDDEN,
            )

        serializer: RoomCreateUpdateSerializer = RoomCreateUpdateSerializer(
            room, data=request.data
        )
        if serializer.is_valid():
            updated: Room = serializer.save()
            return DRFResponse(RoomDetailSerializer(updated).data, status=HTTP_200_OK)
        return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={
            HTTP_200_OK: RoomDetailSerializer,
            HTTP_404_NOT_FOUND: ErrorDetailSerializer,
        },
        description="Retrieve details of a specific room.",
        summary="Get Room Details",
        parameters=[
            OpenApiParameter(
                name="id",
                description="The primary key of the room to retrieve.",
                required=True,
                location=OpenApiParameter.PATH,
                type=int,
            )
        ],
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="details",
        url_name="details",
        permission_classes=[AllowAny],
    )
    def room_details(
        self,
        request: DRFRequest,
        pk: int,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """
        Handle GET request to retrieve details of a specific room.
        args:
            request (DRFRequest): The incoming request to retrieve room details.
            pk (int): The primary key of the room to retrieve.
        returns:
            DRFResponse: The response containing the room details or error message if not found.
        """
        try:
            room: Room = Room.objects.select_related("hotel").get(pk=pk)
        except Room.DoesNotExist:
            return DRFResponse({"detail": "Room not found."}, status=HTTP_404_NOT_FOUND)
        return DRFResponse(RoomDetailSerializer(room).data, status=HTTP_200_OK)

    @extend_schema(
        responses={HTTP_200_OK: RoomDetailSerializer(many=True)},
        description=(
            "List rooms. Query params: hotel, min_price, max_price, "
            "capacity_gte, search, ordering."
        ),
        summary="List Rooms",
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="list",
        url_name="list",
        permission_classes=[AllowAny],
    )
    def list_rooms(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """
        Handle GET request to list rooms with optional filtering and ordering.
        args:
            request (DRFRequest): The incoming request containing query parameters for filtering and ordering.
        returns:
            DRFResponse: The response containing a list of rooms matching the criteria.
        """
        qs: QuerySet[Room] = Room.objects.select_related("hotel", "hotel__owner").all()

        hotel: int | None = request.query_params.get("hotel")
        min_price: float | None = request.query_params.get("min_price")
        max_price: float | None = request.query_params.get("max_price")
        capacity_gte: int | None = request.query_params.get("capacity_gte")
        search: str | None = request.query_params.get("search")
        ordering: str | None = request.query_params.get("ordering")

        if hotel:
            qs = qs.filter(hotel_id=hotel)
        if min_price:
            qs = qs.filter(price_per_night__gte=min_price)
        if max_price:
            qs = qs.filter(price_per_night__lte=max_price)
        if capacity_gte:
            qs = qs.filter(capacity__gte=capacity_gte)
        if search:
            qs = qs.filter(title__icontains=search)

        allowed_ordering = {
            "price_per_night",
            "-price_per_night",
            "capacity",
            "-capacity",
            "created_at",
            "-created_at",
        }
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        data: list[dict] = RoomDetailSerializer(qs, many=True).data
        return DRFResponse(data, status=HTTP_200_OK)

    @extend_schema(
        responses={
            HTTP_204_NO_CONTENT: MessageSerializer,
            HTTP_403_FORBIDDEN: ErrorDetailSerializer,
            HTTP_404_NOT_FOUND: ErrorDetailSerializer,
        },
        description="Delete a room (only hotel owner). Requires auth.",
        summary="Delete Room",
        parameters=[
            OpenApiParameter(
                name="id",
                description="The primary key of the room to delete.",
                required=True,
                location=OpenApiParameter.PATH,
                type=int,
            )
        ],
    )
    @action(
        detail=True,
        methods=["delete"],
        url_path="delete",
        url_name="delete",
        permission_classes=[IsOwner],
    )
    def delete_room(
        self,
        request: DRFRequest,
        pk: int,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """
        Handle DELETE request to delete a specific room. Only the hotel owner can delete rooms.
        args:
            request (DRFRequest): The incoming request to delete a room.
            pk (int): The primary key of the room to delete.
        returns:
            DRFResponse: The response indicating success or failure of the delete operation.
        """
        try:
            room: Room = Room.objects.select_related("hotel", "hotel__owner").get(pk=pk)
        except Room.DoesNotExist:
            return DRFResponse({"detail": "Room not found."}, status=HTTP_404_NOT_FOUND)

        # if room.hotel.owner_id != request.user.id:
        #     return DRFResponse(
        #         {"detail": "You do not have permission to delete this room."},
        #         status=HTTP_403_FORBIDDEN,
        #     )

        room.delete()
        return DRFResponse(
            {"detail": "Room deleted successfully."}, status=HTTP_204_NO_CONTENT
        )

