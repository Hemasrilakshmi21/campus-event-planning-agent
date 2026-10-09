
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from database import get_events_on_date

# Use Indian Standard Time, regardless of Railway's server timezone.
india_tz = ZoneInfo("Asia/Kolkata")


def get_current_time():
    return datetime.now(india_tz)


def calculator_tool(total_budget, audience):
    # Simple deterministic budget calculation.
    percentages = {
        "Venue & setup": 0.25,
        "Food & refreshments": 0.25,
        "Marketing": 0.10,
        "Equipment": 0.15,
        "Certificates & prizes": 0.10,
        "Contingency": 0.15,
    }

    breakdown = []

    for category, percentage in percentages.items():
        amount = round(total_budget * percentage, 2)
        breakdown.append({
            "Category": category,
            "Percentage": f"{percentage * 100:.0f}%",
            "Amount": f"₹{amount:,.2f}",
        })

    return {
        "total": round(total_budget, 2),
        "audience": audience,
        "breakdown": breakdown,
        "message": (
            f"Budget calculated for {audience} expected participants."
        ),
    }


def parse_time(value):
    """
    Accept time objects and strings in either format:
    24-hour: 09:00, 14:30, 18:00
    12-hour: 09:00 AM, 02:30 PM, 06:00 PM
    """
    if isinstance(value, time):
        return value

    if not isinstance(value, str):
        raise ValueError("Time must be a string or datetime.time object.")

    value = value.strip()

    for fmt in ("%H:%M", "%I:%M %p"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue

    raise ValueError(
        f"Invalid time '{value}'. Use HH:MM or HH:MM AM/PM format."
    )


def calendar_tool(event_date, venue, start_time, end_time):
    # Convert string dates to date objects if necessary.
    if isinstance(event_date, str):
        event_date = datetime.strptime(
            event_date.strip(), "%Y-%m-%d"
        ).date()
    elif isinstance(event_date, datetime):
        event_date = event_date.date()

    # Accept both 24-hour and 12-hour time formats.
    start_time = parse_time(start_time)
    end_time = parse_time(end_time)

    # Validate the event time range.
    if start_time >= end_time:
        return {
            "available": False,
            "conflicts": ["End time must be after start time."],
            "checked_date": str(event_date),
            "venue": venue,
            "start_time": start_time.strftime("%I:%M %p"),
            "end_time": end_time.strftime("%I:%M %p"),
        }

    existing = get_events_on_date(event_date)
    conflicts = []

    for event in existing:
        existing_venue = event.get("venue", "")

        if existing_venue.strip().lower() != venue.strip().lower():
            continue

        # Parse previously stored times in either format.
        old_start = parse_time(event["start_time"])
        old_end = parse_time(event["end_time"])

        # Check whether the time ranges overlap.
        if start_time < old_end and end_time > old_start:
            conflicts.append(
                f"{event['event_name']} already uses {venue} "
                f"from {old_start.strftime('%I:%M %p')} "
                f"to {old_end.strftime('%I:%M %p')}."
            )

    return {
        "available": len(conflicts) == 0,
        "conflicts": conflicts,
        "checked_date": str(event_date),
        "venue": venue,
        "start_time": start_time.strftime("%I:%M %p"),
        "end_time": end_time.strftime("%I:%M %p"),
    }


def is_valid_date(event_date):
    # Compare against today's date in India, not Railway's server timezone.
    if isinstance(event_date, str):
        event_date = datetime.strptime(
            event_date.strip(), "%Y-%m-%d"
        ).date()
    elif isinstance(event_date, datetime):
        event_date = event_date.date()

    today_in_india = datetime.now(india_tz).date()

    return event_date >= today_in_india
