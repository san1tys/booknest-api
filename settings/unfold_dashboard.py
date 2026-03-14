from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.http import HttpRequest
from django.utils import timezone

from apps.bookings.models import Booking, BookingStatus
from apps.hotels.models import Hotel


def dashboard_callback(request: HttpRequest, context: dict[str, Any]) -> dict[str, Any]:
    """
    Inject earnings data into Unfold admin index context.

    Earnings are calculated per night (each day in [check_in, check_out))
    using the booked room's price_per_night.
    """

    if not getattr(request.user, "is_staff", False):
        return context

    try:
        weeks = int(request.GET.get("weeks", 12))
    except (TypeError, ValueError):
        weeks = 12

    weeks = max(4, min(weeks, 52))

    end_date = timezone.localdate()
    period_end_exclusive = end_date + timedelta(days=1)

    current_week_start = end_date - timedelta(days=end_date.weekday())  # Monday
    start_week_start = current_week_start - timedelta(weeks=weeks - 1)
    start_date = start_week_start

    hotel_names: dict[int, str] = {}
    total_by_hotel: dict[int, Decimal] = {}

    bookings = (
        Booking.objects.filter(
            status__in=(BookingStatus.CONFIRMED, BookingStatus.COMPLETED),
            check_in__lt=period_end_exclusive,
            check_out__gt=start_date,
        )
        .select_related("room", "room__hotel")
        .only(
            "check_in",
            "check_out",
            "room__price_per_night",
            "room__hotel__id",
            "room__hotel__name",
        )
    )

    for booking in bookings:
        if not booking.room_id or not getattr(booking.room, "hotel_id", None):
            continue

        price_per_night = booking.room.price_per_night or Decimal("0")
        if price_per_night <= 0:
            continue

        hotel_id = booking.room.hotel_id
        hotel_names[hotel_id] = booking.room.hotel.name

        booking_start = max(booking.check_in, start_date)
        booking_end = min(booking.check_out, period_end_exclusive)
        if booking_end <= booking_start:
            continue

        nights = (booking_end - booking_start).days
        if nights <= 0:
            continue

        total_by_hotel[hotel_id] = total_by_hotel.get(hotel_id, Decimal("0")) + (
            price_per_night * nights
        )

    hotels = list(
        Hotel.objects.only("id", "name").order_by("name").values("id", "name")
    )
    total_period = sum(total_by_hotel.values(), Decimal("0"))

    hotel_rows = []
    for hotel in hotels:
        hotel_id = hotel["id"]
        hotel_name = hotel["name"]
        hotel_total = total_by_hotel.get(hotel_id, Decimal("0"))

        hotel_rows.append([hotel_name, f"{hotel_total:.2f}"])

    hotels_totals_table = {
        "headers": ["Hotel", f"Earnings (last {weeks} weeks)"],
        "rows": hotel_rows,
    }

    context.update(
        {
            "dashboard_weeks": weeks,
            "dashboard_total_period": f"{total_period:.2f}",
            "dashboard_hotels_totals_table": hotels_totals_table,
        }
    )

    return context
