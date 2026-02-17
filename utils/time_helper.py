"""
Timezone utility helpers for the AI journaling app.
Converts UTC times stored in database to local system time for display.
"""

from __future__ import annotations

from datetime import datetime, timezone
import time


def utc_to_local(dt: datetime) -> datetime:
    """
    Convert a UTC datetime (with or without tzinfo) to local system time.
    
    Args:
        dt: datetime object (UTC, aware or naive)
    
    Returns:
        datetime in local system timezone
    """
    if dt is None:
        return datetime.now()
    
    # If naive (no tzinfo), assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Convert to local time
    local_dt = dt.astimezone(tz=None)
    
    return local_dt


def format_local_datetime(dt: datetime, fmt: str = "%b %d, %Y %I:%M %p") -> str:
    """
    Convert UTC datetime to local time and format as string.
    
    Args:
        dt: datetime object (UTC)
        fmt: strftime format string
    
    Returns:
        Formatted local time string
    """
    if dt is None:
        return ""
    
    local_dt = utc_to_local(dt)
    return local_dt.strftime(fmt)


def format_local_date_only(dt: datetime) -> str:
    """
    Convert UTC datetime to local date string (no time).
    
    Args:
        dt: datetime object (UTC)
    
    Returns:
        Formatted date string like "Feb 17, 2026"
    """
    if dt is None:
        return ""
    
    local_dt = utc_to_local(dt)
    return local_dt.strftime("%b %d, %Y")


def to_local_for_chart(dt: datetime) -> datetime:
    """
    Convert UTC datetime to local time for Plotly charts.
    
    Args:
        dt: datetime object (UTC)
    
    Returns:
        Local datetime for chart display
    """
    if dt is None:
        return datetime.now()
    
    return utc_to_local(dt)