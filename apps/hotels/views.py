from typing import Any

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
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
    HTTP_429_TOO_MANY_REQUESTS,
)
from rest_framework.viewsets import ViewSet

from apps.abstract.decorators import (
    find_queryset_object_by_query_pk,
    validate_serializer_data,
)
from apps.abstract.pagination import StandardPagination
from apps.abstract.permissions import IsOwner
from apps.abstract.redis_storage import (
    build_cache_key,
    cache_get,
    cache_set,
)
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
    detail_queryset = Hotel.objects.select_related("owner")

    @extend_schema(
        request=HotelCreateUpdateSerializer,
        responses={
            HTTP_201_CREATED: HotelDetailSerializer,
            HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            HTTP_401_UNAUTHORIZED: ErrorDetailSerializer,
            HTTP_405_METHOD_NOT_ALLOWED: ErrorDetailSerializer,
            HTTP_429_TOO_MANY_REQUESTS: ErrorDetailSerializer,
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
    @validate_serializer_data(HotelCreateUpdateSerializer)
    def create_hotel(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        serializer: HotelCreateUpdateSerializer,
        **kwargs: dict[str, Any],
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
        hotel = serializer.save(owner=request.user)
        return DRFResponse(HotelDetailSerializer(hotel).data, status=HTTP_201_CREATED)

    @extend_schema(
        request=HotelCreateUpdateSerializer,
        responses={
            HTTP_200_OK: HotelDetailSerializer,
            HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            HTTP_401_UNAUTHORIZED: ErrorDetailSerializer,
            HTTP_403_FORBIDDEN: ErrorDetailSerializer,
            HTTP_404_NOT_FOUND: ErrorDetailSerializer,
            HTTP_405_METHOD_NOT_ALLOWED: ErrorDetailSerializer,
            HTTP_429_TOO_MANY_REQUESTS: ErrorDetailSerializer,
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
        permission_classes=[IsAuthenticated, IsOwner],
    )
    @find_queryset_object_by_query_pk(detail_queryset, "Hotel")
    @validate_serializer_data(HotelCreateUpdateSerializer)
    def update_hotel(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        object: Hotel,
        serializer: HotelCreateUpdateSerializer,
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """
        Handle PUT request to update an existing hotel.
        Args:
            request (DRFRequest): The incoming request object containing updated hotel data.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.
        Returns:
            DRFResponse: A response object containing the updated hotel data or error details.
        """
        self.check_object_permissions(request, object)
        updated_hotel = serializer.save()
        return DRFResponse(
            HotelDetailSerializer(updated_hotel).data, status=HTTP_200_OK
        )

    @extend_schema(
        responses={
            HTTP_200_OK: HotelDetailSerializer,
            HTTP_404_NOT_FOUND: ErrorDetailSerializer,
            HTTP_429_TOO_MANY_REQUESTS: ErrorDetailSerializer,
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
    @find_queryset_object_by_query_pk(detail_queryset, "Hotel")
    def hotel_details(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        object: Hotel,
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """
        Handle GET request to retrieve details of a specific hotel.
        Args:
            request (DRFRequest): The incoming request object.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.
        Returns:
            DRFResponse: A response object containing the hotel details or error details.
        """
        cache_key = build_cache_key("hotels:detail", object.pk)
        cached_data = cache_get(cache_key)
        if cached_data is not None:
            return DRFResponse(cached_data, status=HTTP_200_OK)

        data = HotelDetailSerializer(object).data
        cache_set(cache_key, data)
        return DRFResponse(data, status=HTTP_200_OK)

    @extend_schema(
        responses={
            HTTP_200_OK: HotelDetailSerializer(many=True),
            HTTP_405_METHOD_NOT_ALLOWED: ErrorDetailSerializer,
            HTTP_429_TOO_MANY_REQUESTS: ErrorDetailSerializer,
        },
        description="Retrieve a list of all hotels.",
        summary="List Hotels",
        parameters=[
            OpenApiParameter("page", int, description="Page number"),
            OpenApiParameter(
                "page_size", int, description="Results per page (max 100)"
            ),
        ],
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
            DRFResponse: A response object containing a paginated list of hotels.
        """

        cache_key = build_cache_key("hotels:list", request.get_full_path())
        cached_data = cache_get(cache_key)
        if cached_data is not None:
            return DRFResponse(cached_data, status=HTTP_200_OK)

        hotels: QuerySet[Hotel] = (
            Hotel.objects.select_related("owner").all().order_by("pk")
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(hotels, request, view=self)
        serializer: HotelDetailSerializer = HotelDetailSerializer(page, many=True)
        response: DRFResponse = paginator.get_paginated_response(serializer.data)
        cache_set(cache_key, response.data)
        return response

    @extend_schema(
        responses={
            HTTP_204_NO_CONTENT: MessageSerializer,
            HTTP_401_UNAUTHORIZED: ErrorDetailSerializer,
            HTTP_404_NOT_FOUND: ErrorDetailSerializer,
            HTTP_403_FORBIDDEN: ErrorDetailSerializer,
            HTTP_429_TOO_MANY_REQUESTS: ErrorDetailSerializer,
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
        permission_classes=[IsAuthenticated, IsOwner],
    )
    @find_queryset_object_by_query_pk(detail_queryset, "Hotel")
    def delete_hotel(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        object: Hotel,
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """
        Handle DELETE request to delete a specific hotel.
        Args:
            request (DRFRequest): The incoming request object.
            args (tuple): Additional positional arguments.
            kwargs (dict): Additional keyword arguments.
        Returns:
            DRFResponse: A response object indicating the success or failure of the deletion.
        """
        self.check_object_permissions(request, object)
        object.delete()
        return DRFResponse(
            {"detail": _("Hotel deleted successfully.")},
            status=HTTP_204_NO_CONTENT,
        )
