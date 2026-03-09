from typing import Any

from rest_framework.viewsets import ViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_205_RESET_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_404_NOT_FOUND,
)

from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema

from apps.hotels.serializers import (
    HotelCreateUpdateSerializer, 
    HotelDetailSerializer
)
from apps.users.models import User
from apps.hotels.models import Hotel

from apps.abstract.serializers import ErrorDetailSerializer, MessageSerializer, ValidationErrorSerializer

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
        examples=[
            {
                "name": "Hotel California",
                "description": "A lovely place with a lovely face.",
                "address": "42 Sunset Boulevard",
                "city": "Los Angeles",
                "owner": 1
            }
        ],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="create",
        url_name="create",
        permission_classes=[IsAuthenticated],
    )
    def create_hotel(self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> DRFResponse:
        """
        Handle POST request to create a new hotel.
        Args:
            request (DRFRequest): The incoming request object containing hotel data.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.
        Returns:
            DRFResponse: A response object containing the created hotel data or error details.
        """

        serializer: HotelCreateUpdateSerializer = HotelCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            hotel: Hotel = serializer.save()
            return DRFResponse(HotelDetailSerializer(hotel).data, status=HTTP_201_CREATED)
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
        examples=[
            {
                "name": "Hotel California Updated",
                "description": "An updated description for the lovely place.",
                "address": "42 Sunset Boulevard",
            }
        ],
    )
    @action(
        detail=True,
        methods=["put"],
        url_path="update",
        url_name="update",
        permission_classes=[IsAuthenticated],
    )
    def update_hotel(self, request: DRFRequest, pk: int, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> DRFResponse:
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
            return DRFResponse({"detail": "Hotel not found."}, status=HTTP_404_NOT_FOUND)

        if hotel.owner != request.user:
            return DRFResponse({"detail": "You do not have permission to edit this hotel."}, status=HTTP_403_FORBIDDEN)

        serializer: HotelCreateUpdateSerializer = HotelCreateUpdateSerializer(hotel, data=request.data)
        if serializer.is_valid():
            updated_hotel: Hotel = serializer.save()
            return DRFResponse(HotelDetailSerializer(updated_hotel).data, status=HTTP_200_OK)
        return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)