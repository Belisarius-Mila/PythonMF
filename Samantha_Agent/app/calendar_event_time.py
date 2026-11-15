"""Canonical all-day boundaries; preserve exact native instants elsewhere.

Apple TN3130: modern EventKit returns 23:59:59 on the final day,
where older versions returned midnight on the following day.
"""
from datetime import datetime, timedelta, timezone
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def event_zone(name):
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        fixed = re.fullmatch(r"GMT([+-])(\d{2})(\d{2})", name)
        if not fixed:
            raise
        sign, hours, minutes = fixed.groups()
        hours, minutes = int(hours), int(minutes)
        if hours > 23 or minutes > 59:
            raise ValueError("Invalid fixed calendar time zone")
        return timezone(timedelta(minutes=(hours * 60 + minutes) * (1 if sign == '+' else -1)))


def exclusive_all_day_end(value: datetime, *, all_day: bool, time_zone: str) -> datetime:
    if not all_day:
        return value
    local = value.astimezone(event_zone(time_zone))
    if (local.hour, local.minute, local.second, local.microsecond) == (23, 59, 59, 0):
        return value + timedelta(seconds=1)
    return value
