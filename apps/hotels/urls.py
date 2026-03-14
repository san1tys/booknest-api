# Django modules
from django.urls import include, path

# Django Rest Framework modules
from rest_framework.routers import DefaultRouter

# Project modules
from apps.hotels.views import HotelViewSet

router: DefaultRouter = DefaultRouter(trailing_slash=False)

router.register(
    prefix="hotels",
    viewset=HotelViewSet,
    basename="hotel",
)


urlpatterns = [
    path("v1/", include(router.urls)),
]
