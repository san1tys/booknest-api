from django.contrib import admin

from apps.hotels.models import Hotel

# Register your models here.
@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "rating")
    search_fields = ("name", "city")
    list_filter = ("city", "rating")
    fieldsets = (
        (None, {"fields": ("name", "address", "city", "rating", "description")}),
    )
    