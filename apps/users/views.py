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
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_404_NOT_FOUND,
)

from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema

from apps.users.models import User
from apps.users.serializers import (
    UserLoginSerializer,
    UserLoginSuccessSerializer,
    UserRegisterSerializer,
    UserSerializer,
)
from apps.abstract.serializers import ErrorDetailSerializer, MessageSerializer, ValidationErrorSerializer


class UserViewSet(ViewSet):
    permission_classes = [AllowAny]

    # Get user
    @extend_schema(
        summary="Get user details",
        description="Retrieve details of the authenticated user.",
        responses={
            HTTP_200_OK: UserSerializer,
            HTTP_401_UNAUTHORIZED: ErrorDetailSerializer,
        },
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_name="me",
        url_path="me",
    )
    def me(self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> DRFResponse:
        """
        Handle GET request for user details.

        Args:
            request (DRFRequest): The incoming request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            DRFResponse: 
                A response containing the user details or an error message.
        """
        if not request.user.is_authenticated:
            return DRFResponse({"detail": "Authentication credentials were not provided."}, status=HTTP_401_UNAUTHORIZED)
        user = request.user 
        serializer = UserSerializer(user)
        return DRFResponse(serializer.data, status=HTTP_200_OK)

    # Register user
    @extend_schema(
        summary="Register a new user",
        description="Create a new user account with the provided email and password.",
        request=UserRegisterSerializer,
        responses={
            HTTP_201_CREATED: UserSerializer,
            HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            HTTP_401_UNAUTHORIZED: ErrorDetailSerializer,
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[AllowAny],
        url_name="register",
        url_path="register",
    )
    def register(self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> DRFResponse:
        """
        Handle POST request for user registration.

        Args:
            request (DRFRequest): The incoming request object containing user registration data.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        Returns:
            DRFResponse: 
                A response containing the newly created user details or validation errors.
        """
        if request.user.is_authenticated:
            return DRFResponse({"detail": "You are already authenticated."}, status=HTTP_401_UNAUTHORIZED)
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response_serializer = UserSerializer(user)
            return DRFResponse(response_serializer.data, status=HTTP_201_CREATED)
        return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)
    
    # Login user
    @extend_schema(
        summary="Login user",
        description="Authenticate a user and return access and refresh tokens.",
        request=UserLoginSerializer,
        responses={
            HTTP_200_OK: UserLoginSuccessSerializer,
            HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            HTTP_401_UNAUTHORIZED: ErrorDetailSerializer,
            HTTP_405_METHOD_NOT_ALLOWED: ErrorDetailSerializer,
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[AllowAny],
        url_name="login",
        url_path="login",
    )
    def login(self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> DRFResponse:
            """
            Handle POST request for user login.
    
            Args:
                request (DRFRequest): The incoming request object containing user login data.
                *args: Additional positional arguments.
                **kwargs: Additional keyword arguments.
            Returns:
                DRFResponse:
                    A response containing the user details and tokens or validation errors.
            """

            if request.user.is_authenticated:
                return DRFResponse({"detail": "You are already authenticated."}, status=HTTP_405_METHOD_NOT_ALLOWED )
            
            serializer = UserLoginSerializer(data=request.data)
            if serializer.is_valid():
                user: User = User.objects.filter(email=serializer.validated_data["email"]).first()

                if user is None or not user.check_password(serializer.validated_data["password"]):
                    return DRFResponse({"detail": "Invalid email or password."}, status=HTTP_401_UNAUTHORIZED)
                if not user.is_active:
                    return DRFResponse({"detail": "User account is disabled."}, status=HTTP_401_UNAUTHORIZED)
                
                refresh: RefreshToken = RefreshToken.for_user(user)
                response_data = {
                    "email": user.email,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                }
                serializer = UserLoginSuccessSerializer(data=response_data)
                if serializer.is_valid():
                    return DRFResponse(serializer.data, status=HTTP_200_OK)
            return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)