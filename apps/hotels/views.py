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
from apps.hotels.models import Hotel
from apps.hotels.serializers import (
    HotelCreateUpdateSerializer,
    HotelDetailSerializer,
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
