# gramps-mcp - AI-Powered Genealogy Research & Management
# Copyright (C) 2025 cabout.me
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Place data handler for Gramps MCP operations.

Provides clean, direct formatting of place data from handles.
"""

import logging

from ..models.api_calls import ApiCalls

logger = logging.getLogger(__name__)


async def format_place(client, tree_id: str, handle: str, inline: bool = False) -> str:
    """
    Format place data with full hierarchy and details.

    Args:
        client: Gramps API client instance
        tree_id (str): Family tree identifier
        handle (str): Place handle
        inline (bool, optional): If True, return just the hierarchy for inline use

    Returns:
        str: Formatted place string with hierarchy (and details if not inline)
    """
    if not handle:
        return "" if inline else "• **Place**\n  No handle provided\n\n"

    try:
        place_data = await client.make_api_call(
            api_call=ApiCalls.GET_PLACE, tree_id=tree_id, handle=handle
        )
        if not place_data:
            return "" if inline else f"• **Place {handle}**\n  Place not found\n\n"

        # Build place hierarchy
        place_hierarchy = await _build_place_hierarchy(client, tree_id, place_data)

        # For inline use, just return the hierarchy
        if inline:
            return place_hierarchy if place_hierarchy else ""

        # For search results, return new format
        gramps_id = place_data.get("gramps_id", "")
        place_type = place_data.get("place_type", "")
        urls = place_data.get("urls", [])

        # First line: type: title (full hierarchy) - gramps_id - [handle]
        title = place_hierarchy if place_hierarchy else ""
        first_line = f"{place_type}: {title} - {gramps_id} - [{handle}]"
        result = first_line

        # Second line: url path - url desc (if URLs present)
        for url in urls:
            if isinstance(url, dict):
                url_path = url.get("path", "")
                url_desc = url.get("description", "")
                if url_path:
                    url_line = url_path
                    if url_desc:
                        url_line += f" - {url_desc}"
                    result += f"\n{url_line}"

        return result + "\n\n"

    except Exception as e:
        logger.debug(f"Failed to format place {handle}: {e}")
        if inline:
            return ""
        else:
            return f"• **Place {handle}**\n  Error formatting place: {str(e)}\n\n"


async def _build_place_hierarchy(client, tree_id: str, place_data: dict) -> str:
    """Build place hierarchy string from place data."""
    # The title field contains the full hierarchy
    title = place_data.get("title", "")
    if title:
        return title

    # If no title, build from name and parent places
    place_names = []

    # Get current place name
    name_value = place_data.get("name", {}).get("value", "")
    if name_value:
        place_names.append(name_value)

    # Follow parent places
    placeref_list = place_data.get("placeref_list", [])

    while placeref_list:
        parent_handle = placeref_list[0].get("ref")
        if not parent_handle:
            break

        parent_data = await client.make_api_call(
            api_call=ApiCalls.GET_PLACE, tree_id=tree_id, handle=parent_handle
        )
        if not parent_data:
            break

        # Check if parent has a title (full hierarchy)
        parent_title = parent_data.get("title", "")
        if parent_title:
            place_names.append(parent_title)
            break

        # Otherwise get parent name
        parent_name = parent_data.get("name", {}).get("value", "")
        if parent_name:
            place_names.append(parent_name)

        # Continue up the hierarchy
        placeref_list = parent_data.get("placeref_list", [])

    return ", ".join(place_names) if place_names else ""
