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
Note data handler for Gramps MCP operations.

Provides clean, direct formatting of note data from handles.
"""

import logging

logger = logging.getLogger(__name__)

# Constants
MAX_NOTE_LENGTH = 500


async def format_note(client, tree_id: str, handle: str) -> str:
    """
    Format note data with text content and type.

    Args:
        client: Gramps API client instance
        tree_id: Family tree identifier
        handle: Note handle

    Returns:
        Formatted note string with content
    """
    if not handle:
        return ""

    try:
        from ..models.api_calls import ApiCalls

        note_data = await client.make_api_call(
            api_call=ApiCalls.GET_NOTE, tree_id=tree_id, handle=handle
        )
        if not note_data:
            return ""

        gramps_id = note_data.get("gramps_id")
        note_type = note_data.get("type")
        text = note_data.get("text", {}).get("string")

        if not text:
            return ""

        # Clean up text - remove excessive whitespace but preserve paragraph breaks
        text = text.strip()

        # Truncate if too long
        if len(text) > MAX_NOTE_LENGTH:
            text = text[: MAX_NOTE_LENGTH - 3] + "..."

        return f"{note_type} Note - {gramps_id} - [{handle}]\n{text}\n\n"

    except Exception as e:
        logger.debug(f"Failed to format note {handle}: {e}")
        return ""
