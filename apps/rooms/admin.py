from django.contrib import admin

from apps.rooms.models import Room


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
