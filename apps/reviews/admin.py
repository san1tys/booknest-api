from django.contrib import admin

from apps.reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "hotel", "user", "rating", "created_at")
    search_fields = ("hotel__name", "user__email", "text")
    list_filter = ("rating", "created_at")

