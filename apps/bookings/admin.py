from django.contrib import admin

from apps.bookings.models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "room",
        "check_in",
        "check_out",
        "status",
        "total_price",
        "created_at",
    )
    list_filter = ("status", "check_in", "check_out", "created_at")
    search_fields = ("user__email", "room__title", "room__hotel__name")
    raw_id_fields = ("user", "room")
