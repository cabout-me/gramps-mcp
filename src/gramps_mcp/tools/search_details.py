"""
Detail retrieval MCP tools for genealogy operations.

This module contains 2 detail retrieval tools for getting comprehensive
person and family information using direct API calls.
"""

import logging
from typing import Dict, List

from mcp.types import TextContent

from ..client import GrampsAPIError
from ..config import get_settings
from ..handlers.family_detail_handler import format_family_detail
from ..handlers.person_detail_handler import format_person_detail
from .search_basic import with_client

logger = logging.getLogger(__name__)


def _format_error_response(error: Exception, operation: str) -> List[TextContent]:
    """Format error into user-friendly MCP response."""
    if isinstance(error, GrampsAPIError):
        error_msg = str(error)
    else:
        error_msg = f"Unexpected error during {operation}: {str(error)}"

    logger.error(f"Tool error in {operation}: {error_msg}")
    return [TextContent(type="text", text=f"Error: {error_msg}")]


@with_client
async def get_person_tool(client, arguments: Dict) -> List[TextContent]:
    """
    Get comprehensive person information using direct API calls.
    """
    try:
        # Extract handle from arguments
        handle = arguments.get("person_handle")
        if not handle:
            raise ValueError("person_handle is required")

        # Get tree_id from settings
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Use the detailed person handler to get comprehensive formatted data
        formatted_person = await format_person_detail(client, tree_id, handle)

        return [TextContent(type="text", text=formatted_person)]

    except Exception as e:
        return _format_error_response(e, "person details retrieval")


@with_client
async def get_family_tool(client, arguments: Dict) -> List[TextContent]:
    """
    Get detailed family information using direct API calls.
    """
    try:
        # Extract handle from arguments
        handle = arguments.get("family_handle")
        if not handle:
            raise ValueError("family_handle is required")

        # Get tree_id from settings
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Use the detailed family handler to get comprehensive formatted data
        formatted_family = await format_family_detail(client, tree_id, handle)

        return [TextContent(type="text", text=formatted_family)]

    except Exception as e:
        return _format_error_response(e, "family details retrieval")


async def get_type_tool(arguments: Dict) -> List[TextContent]:
    """Universal get tool for person and family details."""
    entity_type = arguments.get("type")
    handle = arguments.get("handle")
    gramps_id = arguments.get("gramps_id")

    # If gramps_id provided but no handle, find the handle first
    if gramps_id and not handle:
        from .search_basic import find_type_tool

        search_result = await find_type_tool(
            {"type": entity_type, "gql": f'gramps_id="{gramps_id}"', "max_results": 1}
        )

        # Extract handle from search result
        search_text = search_result[0].text
        import re

        handle_match = re.search(r"\[([^\]]+)\]", search_text)
        if handle_match:
            handle = handle_match.group(1)

    if entity_type == "person" and handle:
        return await get_person_tool({"person_handle": handle})
    elif entity_type == "family" and handle:
        return await get_family_tool({"family_handle": handle})

    return [TextContent(type="text", text="get_type_tool not yet implemented")]
