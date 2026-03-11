# Django modules
from django.urls import include, path

# Django Rest Framework modules
from rest_framework.routers import DefaultRouter

# Project modules
from apps.rooms.views import RoomViewSet

router: DefaultRouter = DefaultRouter(trailing_slash=False)

router.register(
    prefix="rooms",
    viewset=RoomViewSet,
    basename="room",
)

urlpatterns = [
    path("v1/", include(router.urls)),
]
