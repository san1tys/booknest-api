# Django modules
from django.urls import include, path

# Django Rest Framework modules
from rest_framework.routers import DefaultRouter

# Project modules
from apps.bookings.views import BookingViewSet


router: DefaultRouter = DefaultRouter(
    trailing_slash=False
)

router.register(
    prefix="bookings",
    viewset=BookingViewSet,
    basename="booking",
)


urlpatterns = [
    path("v1/", include(router.urls)),
]
