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
Data management MCP tools for genealogy operations.

This module contains 8 CRUD tools for creating and updating people, families,
events, places, sources, citations, notes, and media records.
"""

import logging
from typing import Dict, List

from mcp.types import TextContent

from ..client import GrampsAPIError, GrampsWebAPIClient
from ..config import get_settings
from ..handlers.citation_handler import format_citation
from ..handlers.event_handler import format_event
from ..handlers.family_handler import format_family
from ..handlers.media_handler import format_media
from ..handlers.note_handler import format_note
from ..handlers.person_handler import format_person
from ..handlers.place_handler import format_place
from ..handlers.repository_handler import format_repository
from ..handlers.source_handler import format_source
from ..models.api_calls import ApiCalls
from ..models.parameters.citation_params import CitationData
from ..models.parameters.event_params import EventSaveParams
from ..models.parameters.family_params import FamilySaveParams
from ..models.parameters.media_params import MediaSaveParams
from ..models.parameters.note_params import NoteSaveParams
from ..models.parameters.people_params import PersonData
from ..models.parameters.place_params import PlaceSaveParams
from ..models.parameters.repository_params import RepositoryData
from ..models.parameters.source_params import SourceSaveParams

logger = logging.getLogger(__name__)


def _format_error_response(error: Exception, operation: str) -> List[TextContent]:
    """Format error into user-friendly MCP response."""
    if isinstance(error, GrampsAPIError):
        error_msg = str(error)
    else:
        error_msg = f"Unexpected error during {operation}: {str(error)}"

    logger.error(f"Tool error in {operation}: {error_msg}")
    return [TextContent(type="text", text=f"Error: {error_msg}")]


def _extract_entity_data(result, entity_type: str = None):
    """Extract entity data from API response, handling different formats."""
    if not result:
        return None

    # Handle family creation special case - find Family entry in response list
    if entity_type == "family" and isinstance(result, list) and len(result) > 1:
        family_entry = None
        for entry in result:
            if entry.get("new", {}).get("_class") == "Family":
                family_entry = entry["new"]
                break
        return family_entry if family_entry else result[0].get("new", result[0])

    # Standard case - API may return list or single object
    return (
        result[0]["new"]
        if result and isinstance(result, list) and result[0].get("new")
        else result
    )


async def _handle_crud_operation(
    params, entity_type: str, post_api_call, put_api_call, param_class
) -> List[TextContent]:
    """Common helper for create/update operations."""
    try:
        # Validate parameters
        validated_params = param_class(**params)

        # Get tree_id from settings
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Create client and make unified API call
        client = GrampsWebAPIClient()
        try:
            # Choose API call based on whether handle is provided (update vs create)
            if hasattr(validated_params, "handle") and validated_params.handle:
                # Update existing entity
                result = await client.make_api_call(
                    api_call=put_api_call,
                    params=validated_params,
                    tree_id=tree_id,
                    handle=validated_params.handle,
                )
                operation = "updated"
            else:
                # Create new entity
                result = await client.make_api_call(
                    api_call=post_api_call, params=validated_params, tree_id=tree_id
                )
                operation = "created"

            # Extract entity data from API response
            entity_data = _extract_entity_data(result, entity_type)
            formatted_response = await _format_save_response(
                client, entity_data, entity_type, operation, tree_id
            )
            return [TextContent(type="text", text=formatted_response)]

        finally:
            await client.close()

    except Exception as e:
        return _format_error_response(e, f"{entity_type} save")


async def _format_save_response(
    client: GrampsWebAPIClient,
    entity_data: Dict,
    entity_type: str,
    operation: str,
    tree_id: str,
) -> str:
    """Format successful save operation response using appropriate format handler."""
    handle = entity_data.get("handle", "N/A")
    gramps_id = entity_data.get("gramps_id", "N/A")

    try:
        # Use the appropriate format handler to get consistent formatting
        if entity_type == "person":
            formatted_details = await format_person(client, tree_id, handle)
        elif entity_type == "family":
            formatted_details = await format_family(client, tree_id, handle)
        elif entity_type == "event":
            formatted_details = await format_event(client, tree_id, handle)
        elif entity_type == "place":
            formatted_details = await format_place(client, tree_id, handle)
        elif entity_type == "source":
            formatted_details = await format_source(client, tree_id, handle)
        elif entity_type == "citation":
            formatted_details = await format_citation(client, tree_id, handle)
        elif entity_type == "media":
            formatted_details = await format_media(client, tree_id, handle)
        elif entity_type == "note":
            formatted_details = await format_note(client, tree_id, handle)
        elif entity_type == "repository":
            formatted_details = await format_repository(client, tree_id, handle)
        else:
            # Fallback for unknown types
            formatted_details = (
                f"• **{entity_type.title()} {gramps_id}** " f"(Handle: `{handle}`)\n\n"
            )

        # Add success prefix to the formatted details
        result = f"Successfully {operation} {entity_type}:\n\n{formatted_details}"
        return result

    except Exception as e:
        logger.warning(f"Error formatting {entity_type} details: {e}")
        # Fallback to basic formatting if handler fails
        display_name = f"{entity_type.title()} {gramps_id}"
        result = f"Successfully {operation} {entity_type}: **{display_name}**\n\n"
        result += f"**ID:** {gramps_id}\n"
        result += f"**Handle:** `{handle}`\n"
        return result


# ============================================================================
# Data Management Tools (8 tools)
# ============================================================================


async def create_person_tool(arguments: Dict) -> List[TextContent]:
    """
    Create or update person information including family links and event associations.
    """
    return await _handle_crud_operation(
        arguments, "person", ApiCalls.POST_PEOPLE, ApiCalls.PUT_PERSON, PersonData
    )


async def create_family_tool(arguments: Dict) -> List[TextContent]:
    """
    Create or update family unit including member relationships.
    """
    try:
        # Validate parameters
        params = FamilySaveParams(**arguments)

        # Get tree_id from settings
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Create client and make unified API call
        client = GrampsWebAPIClient()
        try:
            # Choose API call based on whether handle is provided (update vs create)
            if params.handle:
                # Update existing family
                result = await client.make_api_call(
                    api_call=ApiCalls.PUT_FAMILY,
                    params=params,
                    tree_id=tree_id,
                    handle=params.handle,
                )
                operation = "updated"
            else:
                # Create new family
                result = await client.make_api_call(
                    api_call=ApiCalls.POST_FAMILIES, params=params, tree_id=tree_id
                )
                operation = "created"

            # Extract entity data from API response (handles family special case)
            entity_data = _extract_entity_data(result, "family")
            formatted_response = await _format_save_response(
                client, entity_data, "family", operation, tree_id
            )
            return [TextContent(type="text", text=formatted_response)]

        finally:
            await client.close()

    except Exception as e:
        return _format_error_response(e, "family save")


async def create_event_tool(arguments: Dict) -> List[TextContent]:
    """
    Create or update life event including person/place associations.
    """
    return await _handle_crud_operation(
        arguments, "event", ApiCalls.POST_EVENTS, ApiCalls.PUT_EVENT, EventSaveParams
    )


async def create_place_tool(arguments: Dict) -> List[TextContent]:
    """
    Create or update geographic location.
    """
    return await _handle_crud_operation(
        arguments, "place", ApiCalls.POST_PLACES, ApiCalls.PUT_PLACE, PlaceSaveParams
    )


async def create_source_tool(arguments: Dict) -> List[TextContent]:
    """
    Create or update source document.
    """
    return await _handle_crud_operation(
        arguments,
        "source",
        ApiCalls.POST_SOURCES,
        ApiCalls.PUT_SOURCE,
        SourceSaveParams,
    )


async def create_citation_tool(arguments: Dict) -> List[TextContent]:
    """
    Create or update citation including object associations.
    """
    return await _handle_crud_operation(
        arguments,
        "citation",
        ApiCalls.POST_CITATIONS,
        ApiCalls.PUT_CITATION,
        CitationData,
    )


async def create_note_tool(arguments: Dict) -> List[TextContent]:
    """
    Create or update textual note including object associations.
    """
    return await _handle_crud_operation(
        arguments, "note", ApiCalls.POST_NOTES, ApiCalls.PUT_NOTE, NoteSaveParams
    )


async def create_media_tool(arguments: Dict) -> List[TextContent]:
    """
    Create or update media files including object associations.
    """
    import mimetypes
    import os

    try:
        # Extract file_location separately (not part of MediaSaveParams)
        file_location = arguments.get("file_location")

        # All other arguments are for metadata
        media_params = {k: v for k, v in arguments.items() if k != "file_location"}
        params = MediaSaveParams(**media_params) if media_params else None

        settings = get_settings()
        tree_id = settings.gramps_tree_id

        client = GrampsWebAPIClient()
        try:
            # If a handle is provided, we are updating an existing media object
            if params and params.handle:
                result = await client.make_api_call(
                    api_call=ApiCalls.PUT_MEDIA_ITEM,
                    params=params,
                    tree_id=tree_id,
                    handle=params.handle,
                )
                operation = "updated"
                entity_data = _extract_entity_data(result)
            else:
                # If no handle, we are creating a new media object,
                # which requires a file
                if not file_location:
                    raise ValueError("file_location is required to create new media.")
                if not os.path.isfile(file_location):
                    raise FileNotFoundError(f"File not found: {file_location}")

                # 1. Upload the file to create the initial media object
                with open(file_location, "rb") as f:
                    file_content = f.read()
                mime_type, _ = mimetypes.guess_type(file_location)
                if not mime_type:
                    mime_type = "application/octet-stream"

                upload_result = await client.upload_media_file(
                    file_content, mime_type, tree_id
                )

                if not (
                    upload_result
                    and isinstance(upload_result, list)
                    and "new" in upload_result[0]
                ):
                    raise GrampsAPIError(
                        "Media upload did not return the expected new object."
                    )
                initial_media_object = upload_result[0]["new"]
                media_handle = initial_media_object["handle"]

                # 2. Merge initial object with metadata and update via PUT
                final_media_data = initial_media_object.copy()
                if params:
                    final_media_data.update(params.model_dump(exclude_none=True))

                result = await client.make_api_call(
                    api_call=ApiCalls.PUT_MEDIA_ITEM,
                    params=final_media_data,
                    tree_id=tree_id,
                    handle=media_handle,
                )
                operation = "created"
                entity_data = _extract_entity_data(result)

            formatted_response = await _format_save_response(
                client, entity_data, "media", operation, tree_id
            )
            return [TextContent(type="text", text=formatted_response)]

        finally:
            await client.close()

    except Exception as e:
        return _format_error_response(e, "media save")


async def create_repository_tool(arguments: Dict) -> List[TextContent]:
    """
    Create or update repository information.
    """
    try:
        # Let Pydantic model handle parameter validation

        # Assert required parameters
        if not arguments.get("name"):
            return [
                TextContent(
                    type="text",
                    text="Error: 'name' parameter is required for repository",
                )
            ]
        if not arguments.get("type"):
            return [
                TextContent(
                    type="text",
                    text="Error: 'type' parameter is required for repository",
                )
            ]

        # Validate parameters
        params = RepositoryData(**arguments)

        # Get tree_id from settings
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Create client and make unified API call
        client = GrampsWebAPIClient()
        try:
            # Choose API call based on whether handle is provided (update vs create)
            if params.handle:
                # Update existing repository
                result = await client.make_api_call(
                    api_call=ApiCalls.PUT_REPOSITORY,
                    params=params,
                    tree_id=tree_id,
                    handle=params.handle,
                )
                operation = "updated"
            else:
                # Create new repository
                result = await client.make_api_call(
                    api_call=ApiCalls.POST_REPOSITORIES, params=params, tree_id=tree_id
                )
                operation = "created"

            # Extract entity data from API response
            entity_data = _extract_entity_data(result)
            formatted_response = await _format_save_response(
                client, entity_data, "repository", operation, tree_id
            )
            return [TextContent(type="text", text=formatted_response)]

        finally:
            await client.close()

    except Exception as e:
        return _format_error_response(e, "repository save")
