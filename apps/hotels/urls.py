from rest_framework.routers import DefaultRouter

from apps.hotels.views import HotelViewSet, RoomViewSet

router = DefaultRouter()
router.register(r"hotels", HotelViewSet, basename="hotel")
router.register(r"rooms", RoomViewSet, basename="room")

urlpatterns = router.urls

# # Django modules
# from django.urls import include, path

# # Django Rest Framework modules
# from rest_framework.routers import DefaultRouter

# # Project modules
# from apps.users.views import UserViewSet


# router: DefaultRouter = DefaultRouter(
#     trailing_slash=False
# )

# router.register(
#     prefix="hotels",
#     viewset=HotelViewSet,
#     basename="hotel",
# )

# router.register(
#     prefix="rooms",
#     viewset=RoomViewSet,
#     basename="room",
# )

# urlpatterns = [
#     path("v1/", include(router.urls)),
# ]
