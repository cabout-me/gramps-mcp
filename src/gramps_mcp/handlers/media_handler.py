"""
Media data handler for Gramps MCP operations.

Provides clean, direct formatting of media data from handles.
"""

import logging

from ..models.api_calls import ApiCalls
from .date_handler import format_date

logger = logging.getLogger(__name__)


async def format_media(client, tree_id: str, handle: str) -> str:
    """
    Format media data with description, path, and type details.

    Args:
        client: Gramps API client instance
        tree_id: Family tree identifier
        handle: Media handle

    Returns:
        Formatted media string with details
    """
    if not handle:
        return "**Unknown Media**\n  No handle provided\n\n"

    try:
        media_data = await client.make_api_call(
            api_call=ApiCalls.GET_MEDIA_ITEM, tree_id=tree_id, handle=handle
        )
        if not media_data:
            return f"**Media {handle}**\n  Media not found\n\n"

        gramps_id = media_data.get("gramps_id", "N/A")
        desc = media_data.get("desc", "").strip()
        mime = media_data.get("mime", "").strip()
        date_info = media_data.get("date", {})

        # Format description
        formatted_desc = desc if desc else "No description"

        # Format date if present
        formatted_date = ""
        if date_info and isinstance(date_info, dict):
            date_result = format_date(date_info)
            if date_result != "date unknown":
                formatted_date = f" - {date_result}"

        # New format: file type - gramps id - [handle] \n desc - date
        file_type = mime if mime else "unknown type"
        first_line = f"{file_type} - {gramps_id} - [{handle}]"
        second_line = f"{formatted_desc}{formatted_date}"

        return f"{first_line}\n{second_line}\n\n"

    except Exception as e:
        logger.debug(f"Failed to format media {handle}: {e}")
        return f"**Media {handle}**\n  Error formatting media: {str(e)}\n\n"
