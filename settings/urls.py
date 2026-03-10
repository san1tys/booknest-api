# Python modules
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# Django modules
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),

    # JWT Authentication
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # User app
    path('api/user/', view=include('apps.users.urls')),
    # path('api/hotels/', view=include('apps.hotels.urls')),
    # path('api/bookings/', view=include('apps.bookings.urls')),

    path("api/", include("apps.hotels.urls")),
    
    #Bookings app
    path("api/", include("apps.bookings.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)