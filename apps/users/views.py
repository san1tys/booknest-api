from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_401_UNAUTHORIZED,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_405_METHOD_NOT_ALLOWED,
)
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from apps.abstract.redis_storage import (
    request_cache_identifier,
    set_language_preference,
    set_temporary_data,
)
from apps.abstract.serializers import (
    ErrorDetailSerializer,
    ValidationErrorSerializer,
)
from apps.abstract.throttles import RedisScopedRateThrottle
from apps.users.models import User
from apps.users.serializers import (
    DetailResponseSerializer,
    EmailVerificationSerializer,
    LanguagePreferenceSerializer,
    ResendVerificationSerializer,
    UserLoginSerializer,
    UserLoginSuccessSerializer,
    UserRegisterSerializer,
    UserRegisterResponseSerializer,
    UserSerializer,
)
from apps.users.services import (
    delete_email_verification_otp,
    dispatch_email_verification_otp,
    get_email_verification_otp,
)


class UserViewSet(ViewSet):
    """ViewSet for user-related actions like registration, login, and retrieving user details."""

    permission_classes = [AllowAny]
    throttle_scope = None

    # Get user
    @extend_schema(
        summary="Get user details",
        description="Retrieve details of the authenticated user.",
        responses={
            HTTP_200_OK: UserSerializer,
            HTTP_401_UNAUTHORIZED: ErrorDetailSerializer,
            HTTP_429_TOO_MANY_REQUESTS: ErrorDetailSerializer,
        },
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_name="me",
        url_path="me",
    )
    def me(
        self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]
    ) -> DRFResponse:
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
        # if not request.user.is_authenticated:
        #     return DRFResponse(
        #         {"detail": "Authentication credentials were not provided."},
        #         status=HTTP_401_UNAUTHORIZED,
        #     )
        user: User = request.user
        serializer: UserSerializer = UserSerializer(user)
        return DRFResponse(serializer.data, status=HTTP_200_OK)

    # Register user
    @extend_schema(
        summary="Register a new user",
        description="Create a new user account and send an OTP for email verification.",
        request=UserRegisterSerializer,
        responses={
            HTTP_200_OK: DetailResponseSerializer,
            HTTP_201_CREATED: UserRegisterResponseSerializer,
            HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            HTTP_401_UNAUTHORIZED: ErrorDetailSerializer,
            HTTP_429_TOO_MANY_REQUESTS: ErrorDetailSerializer,
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[AllowAny],
        throttle_classes=[RedisScopedRateThrottle],
        throttle_scope="auth",
        url_name="register",
        url_path="register",
    )
    def register(
        self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]
    ) -> DRFResponse:
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
            return DRFResponse(
                {"detail": _("You are already authenticated.")},
                status=HTTP_401_UNAUTHORIZED,
            )
        email = str(request.data.get("email", "")).strip()
        existing_user = User.objects.filter(email__iexact=email).first()
        if existing_user is not None and not existing_user.is_email_verified:
            dispatch_email_verification_otp(existing_user)
            return DRFResponse(
                {"detail": _("Account exists but email is not verified. A new OTP was sent.")},
                status=HTTP_200_OK,
            )

        serializer: UserRegisterSerializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user: User = serializer.save()
            dispatch_email_verification_otp(user)
            response_data = {
                "detail": _("Registration successful. Verify your email with the OTP that was sent."),
                "user": UserSerializer(user).data,
            }
            return DRFResponse(response_data, status=HTTP_201_CREATED)
        return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Verify email with OTP",
        description="Verify a user's email address using the OTP sent during registration.",
        request=EmailVerificationSerializer,
        responses={
            HTTP_200_OK: DetailResponseSerializer,
            HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            HTTP_404_NOT_FOUND: ErrorDetailSerializer,
            HTTP_429_TOO_MANY_REQUESTS: ErrorDetailSerializer,
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[AllowAny],
        throttle_classes=[RedisScopedRateThrottle],
        throttle_scope="auth",
        url_name="verify-email",
        url_path="verify-email",
    )
    def verify_email(
        self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]
    ) -> DRFResponse:
        """Verify a user's email address with an OTP."""
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.filter(
                email__iexact=serializer.validated_data["email"]
            ).first()
            if user is None:
                return DRFResponse(
                    {"detail": _("User with this email was not found.")},
                    status=HTTP_404_NOT_FOUND,
                )
            if user.is_email_verified:
                return DRFResponse(
                    {"detail": _("Email is already verified.")},
                    status=HTTP_200_OK,
                )

            otp = get_email_verification_otp(user.email)
            if otp != serializer.validated_data["otp"]:
                return DRFResponse(
                    {"detail": _("Invalid or expired verification code.")},
                    status=HTTP_400_BAD_REQUEST,
                )

            user.is_email_verified = True
            user.save(update_fields=["is_email_verified"])
            delete_email_verification_otp(user.email)
            return DRFResponse(
                {"detail": _("Email verified successfully.")},
                status=HTTP_200_OK,
            )
        return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Resend email verification OTP",
        description="Send a fresh email verification OTP to an unverified user.",
        request=ResendVerificationSerializer,
        responses={
            HTTP_200_OK: DetailResponseSerializer,
            HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            HTTP_404_NOT_FOUND: ErrorDetailSerializer,
            HTTP_429_TOO_MANY_REQUESTS: ErrorDetailSerializer,
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[AllowAny],
        throttle_classes=[RedisScopedRateThrottle],
        throttle_scope="auth",
        url_name="resend-verification",
        url_path="resend-verification",
    )
    def resend_verification(
        self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]
    ) -> DRFResponse:
        """Resend an email verification OTP to an unverified user."""
        serializer = ResendVerificationSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.filter(
                email__iexact=serializer.validated_data["email"]
            ).first()
            if user is None:
                return DRFResponse(
                    {"detail": _("User with this email was not found.")},
                    status=HTTP_404_NOT_FOUND,
                )
            if user.is_email_verified:
                return DRFResponse(
                    {"detail": _("Email is already verified.")},
                    status=HTTP_400_BAD_REQUEST,
                )

            dispatch_email_verification_otp(user)
            return DRFResponse(
                {"detail": _("A new verification OTP was sent to your email.")},
                status=HTTP_200_OK,
            )
        return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)

    # Login user
    @extend_schema(
        summary="Login user",
        description="Authenticate a verified user and return access and refresh tokens.",
        request=UserLoginSerializer,
        responses={
            HTTP_200_OK: UserLoginSuccessSerializer,
            HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            HTTP_401_UNAUTHORIZED: ErrorDetailSerializer,
            HTTP_405_METHOD_NOT_ALLOWED: ErrorDetailSerializer,
            HTTP_429_TOO_MANY_REQUESTS: ErrorDetailSerializer,
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[AllowAny],
        throttle_classes=[RedisScopedRateThrottle],
        throttle_scope="auth",
        url_name="login",
        url_path="login",
    )
    def login(
        self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]
    ) -> DRFResponse:
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
            return DRFResponse(
                {"detail": _("You are already authenticated.")},
                status=HTTP_405_METHOD_NOT_ALLOWED,
            )

        serializer: UserLoginSerializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user: User = User.objects.filter(
                email__iexact=serializer.validated_data["email"]
            ).first()

            if user is None or not user.check_password(
                serializer.validated_data["password"]
            ):
                return DRFResponse(
                    {"detail": _("Invalid email or password.")},
                    status=HTTP_401_UNAUTHORIZED,
                )
            if not user.is_active:
                return DRFResponse(
                    {"detail": _("User account is disabled.")},
                    status=HTTP_401_UNAUTHORIZED,
                )
            if not user.is_email_verified:
                return DRFResponse(
                    {"detail": _("Email is not verified.")},
                    status=HTTP_401_UNAUTHORIZED,
                )

            refresh: RefreshToken = RefreshToken.for_user(user)
            set_temporary_data(
                "refresh_token",
                str(refresh["jti"]),
                {"user_id": user.pk, "email": user.email},
                timeout=int(refresh.lifetime.total_seconds()),
            )
            response_data: dict[str, Any] = {
                "email": user.email,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
            serializer: UserLoginSuccessSerializer = UserLoginSuccessSerializer(
                data=response_data
            )
            if serializer.is_valid():
                return DRFResponse(serializer.data, status=HTTP_200_OK)
        return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Store language preference",
        description="Store the authenticated user's language selection in Redis.",
        request=LanguagePreferenceSerializer,
        responses={
            HTTP_200_OK: LanguagePreferenceSerializer,
            HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            HTTP_401_UNAUTHORIZED: ErrorDetailSerializer,
            HTTP_429_TOO_MANY_REQUESTS: ErrorDetailSerializer,
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_name="language",
        url_path="language",
    )
    def language(
        self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]
    ) -> DRFResponse:
        """Store the authenticated user's language preference in Redis."""
        serializer = LanguagePreferenceSerializer(data=request.data)
        if serializer.is_valid():
            set_language_preference(
                request_cache_identifier(request),
                serializer.validated_data["language"],
            )
            return DRFResponse(serializer.data, status=HTTP_200_OK)

        return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)
