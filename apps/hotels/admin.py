# apps/hotels/admin.py
from django.contrib import admin

from apps.hotels.models import Hotel


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    """Admin configuration for the Hotel model."""

    list_display = ("name", "city", "rating")
    search_fields = ("name", "city")
    list_filter = ("city", "rating")
    fieldsets = (
        (None, {"fields": ("name", "address", "city", "rating", "description")}),
    )
