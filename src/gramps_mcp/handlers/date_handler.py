"""
Date data handler for Gramps MCP operations.

Provides clean, consistent date formatting from Gramps date objects.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def format_date(date_obj: dict) -> str:
    """
    Format Gramps date object into human-readable string with fallback.

    Args:
        date_obj (dict): Gramps date object with dateval array

    Returns:
        str: Formatted date string or "date unknown" if invalid
    """
    if not date_obj:
        return "date unknown"

    # Try formatted string first
    formatted_date = date_obj.get("string", "")
    if formatted_date:
        return formatted_date

    # Try to extract from dateval
    dateval = date_obj.get("dateval")
    if not dateval or len(dateval) < 3:
        return "date unknown"

    # dateval format is [day, month, year, False]
    day, month, year = dateval[0], dateval[1], dateval[2]
    if year <= 0:
        return "date unknown"

    # Get quality and modifier
    quality = date_obj.get("quality", 0)
    modifier = date_obj.get("modifier", 0)

    # Format the base date
    try:
        if day > 0 and month > 0:
            date_dt = datetime(year, month, day)
            base_date = date_dt.strftime("%d %B %Y")
        elif month > 0:
            date_dt = datetime(year, month, 1)
            base_date = date_dt.strftime("%B %Y")
        else:
            base_date = str(year)
    except (ValueError, TypeError):
        base_date = str(year) if year > 0 else "date unknown"

    # Add modifier prefix
    modifier_prefixes = {
        0: "",  # regular
        1: "before ",
        2: "after ",
        3: "about ",
        4: "between ",  # range
        5: "from ",  # span
        6: "",  # textonly
        7: "from ",
        8: "to ",
    }

    # Add quality suffix
    quality_suffixes = {
        0: "",  # regular
        1: " (estimated)",
        2: " (calculated)",
    }

    prefix = modifier_prefixes.get(modifier, "")
    suffix = quality_suffixes.get(quality, "")

    return f"{prefix}{base_date}{suffix}"
