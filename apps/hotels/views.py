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
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
)
from rest_framework.viewsets import ViewSet

from apps.abstract.serializers import (
    ErrorDetailSerializer,
    MessageSerializer,
    ValidationErrorSerializer,
)
from apps.hotels.models import Hotel, Room
from apps.hotels.serializers import (
    HotelCreateUpdateSerializer,
    HotelDetailSerializer,
    RoomCreateUpdateSerializer,
    RoomDetailSerializer,
)


class HotelViewSet(ViewSet):
    """ViewSet for managing hotels."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=HotelCreateUpdateSerializer,
        responses={
            HTTP_201_CREATED: HotelDetailSerializer,
            HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            HTTP_401_UNAUTHORIZED: ErrorDetailSerializer,
            HTTP_405_METHOD_NOT_ALLOWED: ErrorDetailSerializer,
        },
        description="Create a new hotel with the provided details. Requires authentication.",
        summary="Create Hotel",
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="create",
        url_name="create",
        permission_classes=[IsAuthenticated],
    )
    def create_hotel(
        self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]
    ) -> DRFResponse:
        """
        Handle POST request to create a new hotel.
        Args:
            request (DRFRequest): The incoming request object containing hotel data.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.
        Returns:
            DRFResponse: A response object containing the created hotel data or error details.
        """

        serializer: HotelCreateUpdateSerializer = HotelCreateUpdateSerializer(
            data=request.data
        )
        if serializer.is_valid():
            hotel = serializer.save(owner=request.user)
            return DRFResponse(
                HotelDetailSerializer(hotel).data, status=HTTP_201_CREATED
            )
        return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=HotelCreateUpdateSerializer,
        responses={
            HTTP_200_OK: HotelDetailSerializer,
            HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            HTTP_401_UNAUTHORIZED: ErrorDetailSerializer,
            HTTP_403_FORBIDDEN: ErrorDetailSerializer,
            HTTP_404_NOT_FOUND: ErrorDetailSerializer,
            HTTP_405_METHOD_NOT_ALLOWED: ErrorDetailSerializer,
        },
        description="Update an existing hotel with the provided details. Requires authentication and ownership of the hotel.",
        summary="Update Hotel",
        parameters=[
            OpenApiParameter(
                name="id",
                description="The primary key of the hotel to update.",
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
        permission_classes=[IsAuthenticated],
    )
    def update_hotel(
        self,
        request: DRFRequest,
        pk: int,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """
        Handle PUT request to update an existing hotel.
        Args:
            request (DRFRequest): The incoming request object containing updated hotel data.
            pk (int): The primary key of the hotel to be updated.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.
        Returns:
            DRFResponse: A response object containing the updated hotel data or error details.
        """

        try:
            hotel: Hotel = Hotel.objects.get(pk=pk)
        except Hotel.DoesNotExist:
            return DRFResponse(
                {"detail": "Hotel not found."}, status=HTTP_404_NOT_FOUND
            )

        if hotel.owner != request.user:
            return DRFResponse(
                {"detail": "You do not have permission to edit this hotel."},
                status=HTTP_403_FORBIDDEN,
            )

        serializer: HotelCreateUpdateSerializer = HotelCreateUpdateSerializer(
            hotel, data=request.data
        )
        if serializer.is_valid():
            updated_hotel: Hotel = serializer.save()
            return DRFResponse(
                HotelDetailSerializer(updated_hotel).data, status=HTTP_200_OK
            )
        return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={
            HTTP_200_OK: HotelDetailSerializer,
            HTTP_404_NOT_FOUND: ErrorDetailSerializer,
        },
        description="Retrieve details of a specific hotel by its ID.",
        summary="Get Hotel Details",
        parameters=[
            OpenApiParameter(
                name="id",
                description="The primary key of the hotel to retrieve.",
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
    def hotel_details(
        self,
        request: DRFRequest,
        pk: int,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """
        Handle GET request to retrieve details of a specific hotel.
        Args:
            request (DRFRequest): The incoming request object.
            pk (int): The primary key of the hotel to retrieve.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.
        Returns:
            DRFResponse: A response object containing the hotel details or error details.
        """

        try:
            hotel: Hotel = Hotel.objects.get(pk=pk)
            return DRFResponse(HotelDetailSerializer(hotel).data, status=HTTP_200_OK)
        except Hotel.DoesNotExist:
            return DRFResponse(
                {"detail": "Hotel not found."}, status=HTTP_404_NOT_FOUND
            )

    @extend_schema(
        responses={
            HTTP_200_OK: HotelDetailSerializer(many=True),
            HTTP_405_METHOD_NOT_ALLOWED: ErrorDetailSerializer,
        },
        description="Retrieve a list of all hotels.",
        summary="List Hotels",
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="list",
        url_name="list",
        permission_classes=[AllowAny],
    )
    def list_hotels(
        self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]
    ) -> DRFResponse:
        """
        Handle GET request to list all hotels.
        Args:
            request (DRFRequest): The incoming request object.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.
        Returns:
            DRFResponse: A response object containing a list of hotels.
        """

        hotels: QuerySet[Hotel] = Hotel.objects.all()
        serializer: HotelDetailSerializer = HotelDetailSerializer(hotels, many=True)
        return DRFResponse(serializer.data, status=HTTP_200_OK)

    @extend_schema(
        responses={
            HTTP_204_NO_CONTENT: MessageSerializer,
            HTTP_404_NOT_FOUND: ErrorDetailSerializer,
            HTTP_403_FORBIDDEN: ErrorDetailSerializer,
        },
        description="Delete a specific hotel by its ID. Requires authentication and ownership of the hotel.",
        summary="Delete Hotel",
        parameters=[
            OpenApiParameter(
                name="id",
                description="The primary key of the hotel to delete.",
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
        permission_classes=[IsAuthenticated],
    )
    def delete_hotel(
        self,
        request: DRFRequest,
        pk: int,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """
        Handle DELETE request to delete a specific hotel.
        Args:
            request (DRFRequest): The incoming request object.
            pk (int): The primary key of the hotel to delete.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.
        Returns:
            DRFResponse: A response object indicating the success or failure of the deletion.
        """
        try:
            hotel: Hotel = Hotel.objects.get(pk=pk)
        except Hotel.DoesNotExist:
            return DRFResponse(
                {"detail": "Hotel not found."}, status=HTTP_404_NOT_FOUND
            )

        if hotel.owner != request.user:
            return DRFResponse(
                {"detail": "You do not have permission to delete this hotel."},
                status=HTTP_403_FORBIDDEN,
            )

        hotel.delete()
        return DRFResponse(
            {"detail": "Hotel deleted successfully."}, status=HTTP_204_NO_CONTENT
        )


# ------------------------------------------------------------
# RoomViewSet for managing rooms within hotels
# ------------------------------------------------------------
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
        Handle POST request to create a new room.
        Validates the incoming data, checks hotel ownership, and creates a new room if valid.
        Args:
            request (DRFRequest): The incoming request object containing room data.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.
        Returns:
            DRFResponse: A response object containing the created room data or error details.
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
        permission_classes=[IsAuthenticated],
    )
    def update_room(
        self,
        request: DRFRequest,
        pk: int,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """
        Handle PUT request to update an existing room.
        Args:
            request (DRFRequest): The incoming request object containing updated room data.
            pk (int): The primary key of the room to be updated.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.
        Returns:
            DRFResponse: A response object containing the updated room data or error details.
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
        Args:
            request (DRFRequest): The incoming request object.
            pk (int): The primary key of the room to retrieve.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.
        Returns:
            DRFResponse: A response object containing the room details or an error message.
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
        Args:
            request (DRFRequest): The incoming request object containing query parameters for filtering and ordering.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.
        Returns:
            DRFResponse: A response object containing a list of rooms that match the filtering criteria and ordering.
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
        permission_classes=[IsAuthenticated],
    )
    def delete_room(
        self,
        request: DRFRequest,
        pk: int,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """
        Handle DELETE request to delete a specific room.
        Args:
            request (DRFRequest): The incoming request object.
            pk (int): The primary key of the room to delete.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.
        Returns:
            DRFResponse: A response object indicating the success or failure of the deletion.
        """
        try:
            room: Room = Room.objects.select_related("hotel", "hotel__owner").get(pk=pk)
        except Room.DoesNotExist:
            return DRFResponse({"detail": "Room not found."}, status=HTTP_404_NOT_FOUND)

        if room.hotel.owner_id != request.user.id:
            return DRFResponse(
                {"detail": "You do not have permission to delete this room."},
                status=HTTP_403_FORBIDDEN,
            )

        room.delete()
        return DRFResponse(
            {"detail": "Room deleted successfully."}, status=HTTP_204_NO_CONTENT
        )
