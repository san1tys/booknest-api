# apps/hotels/admin.py
from django.contrib import admin

from apps.hotels.models import Hotel, Review, Room


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "rating")
    search_fields = ("name", "city")
    list_filter = ("city", "rating")
    fieldsets = (
        (None, {"fields": ("name", "address", "city", "rating", "description")}),
    )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "hotel",
        "price_per_night",
        "capacity",
        "quantity",
        "created_at",
    )
    list_filter = ("hotel__city", "capacity", "quantity")
    search_fields = ("title", "hotel__name", "hotel__city")
    raw_id_fields = ("hotel",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "hotel", "user", "rating", "created_at")
    search_fields = ("hotel__name", "user__email", "text")
    list_filter = ("rating", "created_at")
