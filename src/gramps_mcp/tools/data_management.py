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

This module contains CRUD tools for creating and updating people, families,
events, places, sources, citations, notes, media records, and file uploads.
"""

import logging
import mimetypes
import os
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


def _validate_params(arguments, param_class):
    """Validate parameters - skip if already a validated Pydantic model."""
    from pydantic import BaseModel

    if isinstance(arguments, BaseModel):
        return arguments
    return param_class(**arguments)


async def _handle_crud_operation(
    params, entity_type: str, post_api_call, put_api_call, param_class
) -> List[TextContent]:
    """Common helper for create/update operations."""
    try:
        # Validate parameters - skip if already a validated Pydantic model
        validated_params = _validate_params(params, param_class)

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


async def create_family_tool(arguments) -> List[TextContent]:
    """
    Create or update family unit including member relationships.
    """
    try:
        # Validate parameters - handles both dict and BaseModel inputs
        params = _validate_params(arguments, FamilySaveParams)

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


async def create_media_tool(arguments) -> List[TextContent]:
    """
    Create or update media files including object associations.
    """
    import mimetypes
    import os
    from pydantic import BaseModel

    try:
        # Handle both dict and BaseModel inputs
        if isinstance(arguments, BaseModel):
            # Convert to dict for processing
            args_dict = arguments.model_dump()
        else:
            args_dict = arguments

        # Extract file_location separately (not part of MediaSaveParams)
        file_location = args_dict.get("file_location")

        # All other arguments are for metadata
        media_params = {k: v for k, v in args_dict.items() if k != "file_location"}
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


async def create_repository_tool(arguments) -> List[TextContent]:
    """
    Create or update repository information.
    """
    try:
        # Validate parameters - handles both dict and BaseModel inputs
        params = _validate_params(arguments, RepositoryData)

        # Assert required parameters
        if not params.name:
            return [
                TextContent(
                    type="text",
                    text="Error: 'name' parameter is required for repository",
                )
            ]
        if not params.type:
            return [
                TextContent(
                    type="text",
                    text="Error: 'type' parameter is required for repository",
                )
            ]

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


# ============================================================================
# Delete Tools (2 tools)
# ============================================================================


async def delete_person_tool(arguments) -> List[TextContent]:
    """Delete a person by handle."""
    from ..models.parameters.delete_params import DeleteParams

    try:
        params = _validate_params(arguments, DeleteParams)
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        client = GrampsWebAPIClient()
        try:
            await client.make_api_call(
                api_call=ApiCalls.DELETE_PERSON,
                params=None,
                tree_id=tree_id,
                handle=params.handle,
            )
            return [
                TextContent(
                    type="text",
                    text=f"Successfully deleted person with handle: {params.handle}",
                )
            ]
        finally:
            await client.close()
    except Exception as e:
        return _format_error_response(e, "person delete")


async def delete_family_tool(arguments) -> List[TextContent]:
    """Delete a family by handle."""
    from ..models.parameters.delete_params import DeleteParams

    try:
        params = _validate_params(arguments, DeleteParams)
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        client = GrampsWebAPIClient()
        try:
            await client.make_api_call(
                api_call=ApiCalls.DELETE_FAMILY,
                params=None,
                tree_id=tree_id,
                handle=params.handle,
            )
            return [
                TextContent(
                    type="text",
                    text=f"Successfully deleted family with handle: {params.handle}",
                )
            ]
        finally:
            await client.close()
    except Exception as e:
        return _format_error_response(e, "family delete")


async def delete_event_tool(arguments) -> List[TextContent]:
    """Delete an event by handle."""
    from ..models.parameters.delete_params import DeleteParams

    try:
        params = _validate_params(arguments, DeleteParams)
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        client = GrampsWebAPIClient()
        try:
            await client.make_api_call(
                api_call=ApiCalls.DELETE_EVENT,
                params=None,
                tree_id=tree_id,
                handle=params.handle,
            )
            return [
                TextContent(
                    type="text",
                    text=f"Successfully deleted event with handle: {params.handle}",
                )
            ]
        finally:
            await client.close()
    except Exception as e:
        return _format_error_response(e, "event delete")


async def delete_note_tool(arguments) -> List[TextContent]:
    """Delete a note by handle."""
    from ..models.parameters.delete_params import DeleteParams

    try:
        params = _validate_params(arguments, DeleteParams)
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        client = GrampsWebAPIClient()
        try:
            await client.make_api_call(
                api_call=ApiCalls.DELETE_NOTE,
                params=None,
                tree_id=tree_id,
                handle=params.handle,
            )
            return [
                TextContent(
                    type="text",
                    text=f"Successfully deleted note with handle: {params.handle}",
                )
            ]
        finally:
            await client.close()
    except Exception as e:
        return _format_error_response(e, "note delete")


async def delete_citation_tool(arguments) -> List[TextContent]:
    """Delete a citation by handle."""
    from ..models.parameters.delete_params import DeleteParams

    try:
        params = _validate_params(arguments, DeleteParams)
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        client = GrampsWebAPIClient()
        try:
            await client.make_api_call(
                api_call=ApiCalls.DELETE_CITATION,
                params=None,
                tree_id=tree_id,
                handle=params.handle,
            )
            return [
                TextContent(
                    type="text",
                    text=f"Successfully deleted citation with handle: {params.handle}",
                )
            ]
        finally:
            await client.close()
    except Exception as e:
        return _format_error_response(e, "citation delete")


async def delete_source_tool(arguments) -> List[TextContent]:
    """Delete a source by handle."""
    from ..models.parameters.delete_params import DeleteParams

    try:
        params = _validate_params(arguments, DeleteParams)
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        client = GrampsWebAPIClient()
        try:
            await client.make_api_call(
                api_call=ApiCalls.DELETE_SOURCE,
                params=None,
                tree_id=tree_id,
                handle=params.handle,
            )
            return [
                TextContent(
                    type="text",
                    text=f"Successfully deleted source with handle: {params.handle}",
                )
            ]
        finally:
            await client.close()
    except Exception as e:
        return _format_error_response(e, "source delete")


async def delete_place_tool(arguments) -> List[TextContent]:
    """Delete a place by handle."""
    from ..models.parameters.delete_params import DeleteParams

    try:
        params = _validate_params(arguments, DeleteParams)
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        client = GrampsWebAPIClient()
        try:
            await client.make_api_call(
                api_call=ApiCalls.DELETE_PLACE,
                params=None,
                tree_id=tree_id,
                handle=params.handle,
            )
            return [
                TextContent(
                    type="text",
                    text=f"Successfully deleted place with handle: {params.handle}",
                )
            ]
        finally:
            await client.close()
    except Exception as e:
        return _format_error_response(e, "place delete")


async def delete_repository_tool(arguments) -> List[TextContent]:
    """Delete a repository by handle."""
    from ..models.parameters.delete_params import DeleteParams

    try:
        params = _validate_params(arguments, DeleteParams)
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        client = GrampsWebAPIClient()
        try:
            await client.make_api_call(
                api_call=ApiCalls.DELETE_REPOSITORY,
                params=None,
                tree_id=tree_id,
                handle=params.handle,
            )
            return [
                TextContent(
                    type="text",
                    text=f"Successfully deleted repository with handle: {params.handle}",
                )
            ]
        finally:
            await client.close()
    except Exception as e:
        return _format_error_response(e, "repository delete")


async def delete_media_tool(arguments) -> List[TextContent]:
    """Delete a media item by handle."""
    from ..models.parameters.delete_params import DeleteParams

    try:
        params = _validate_params(arguments, DeleteParams)
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        client = GrampsWebAPIClient()
        try:
            await client.make_api_call(
                api_call=ApiCalls.DELETE_MEDIA_ITEM,
                params=None,
                tree_id=tree_id,
                handle=params.handle,
            )
            return [
                TextContent(
                    type="text",
                    text=f"Successfully deleted media with handle: {params.handle}",
                )
            ]
        finally:
            await client.close()
    except Exception as e:
        return _format_error_response(e, "media delete")


# ============================================================================
# Tag Tools (CRUD)
# ============================================================================


async def find_tags_tool(arguments) -> List[TextContent]:
    """Find/list all tags in the database."""
    from ..models.parameters.tag_params import TagSearchParams

    try:
        params = _validate_params(arguments, TagSearchParams)
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        client = GrampsWebAPIClient()
        try:
            tags = await client.make_api_call(
                api_call=ApiCalls.GET_TAGS,
                params=params,
                tree_id=tree_id,
            )

            if not tags:
                return [TextContent(type="text", text="No tags found.")]

            result = f"Found {len(tags)} tags:\n\n"
            for tag in tags:
                name = tag.get("name", "Unnamed")
                handle = tag.get("handle", "N/A")
                color = tag.get("color", "")
                priority = tag.get("priority", "")

                result += f"- **{name}** [`{handle}`]"
                if color:
                    result += f" - Color: {color}"
                if priority:
                    result += f" - Priority: {priority}"
                result += "\n"

            return [TextContent(type="text", text=result)]

        finally:
            await client.close()
    except Exception as e:
        return _format_error_response(e, "tags search")


async def create_tag_tool(arguments) -> List[TextContent]:
    """Create or update a tag."""
    from ..models.parameters.tag_params import TagSaveParams

    try:
        params = _validate_params(arguments, TagSaveParams)
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        client = GrampsWebAPIClient()
        try:
            if params.handle:
                # Update existing tag
                result = await client.make_api_call(
                    api_call=ApiCalls.PUT_TAG,
                    params=params,
                    tree_id=tree_id,
                    handle=params.handle,
                )
                operation = "updated"
            else:
                # Create new tag
                result = await client.make_api_call(
                    api_call=ApiCalls.POST_TAGS,
                    params=params,
                    tree_id=tree_id,
                )
                operation = "created"

            # Extract tag data
            if isinstance(result, list) and result:
                tag_data = result[0].get("new", result[0])
            else:
                tag_data = result

            name = tag_data.get("name", params.name)
            handle = tag_data.get("handle", "N/A")

            return [
                TextContent(
                    type="text",
                    text=f"Successfully {operation} tag: **{name}** [`{handle}`]",
                )
            ]

        finally:
            await client.close()
    except Exception as e:
        return _format_error_response(e, "tag save")


async def delete_tag_tool(arguments) -> List[TextContent]:
    """Delete a tag by handle."""
    from ..models.parameters.delete_params import DeleteParams

    try:
        params = _validate_params(arguments, DeleteParams)
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        client = GrampsWebAPIClient()
        try:
            await client.make_api_call(
                api_call=ApiCalls.DELETE_TAG,
                params=None,
                tree_id=tree_id,
                handle=params.handle,
            )
            return [
                TextContent(
                    type="text",
                    text=f"Successfully deleted tag with handle: {params.handle}",
                )
            ]
        finally:
            await client.close()
    except Exception as e:
        return _format_error_response(e, "tag delete")


# ============================================================================
# Media File Tools
# ============================================================================


async def get_media_file_tool(arguments) -> List[TextContent]:
    """
    Get information about a media file (metadata and download URL).

    Note: This returns file metadata. The actual file can be accessed
    via the Gramps Web UI or API directly.
    """
    from ..models.parameters.delete_params import DeleteParams

    try:
        params = _validate_params(arguments, DeleteParams)
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        client = GrampsWebAPIClient()
        try:
            # First get media metadata
            media_info = await client.make_api_call(
                api_call=ApiCalls.GET_MEDIA_ITEM,
                params=None,
                tree_id=tree_id,
                handle=params.handle,
            )

            if not media_info:
                return [
                    TextContent(type="text", text=f"Media not found: {params.handle}")
                ]

            # Format response
            gramps_id = media_info.get("gramps_id", "N/A")
            desc = media_info.get("desc", "No description")
            mime = media_info.get("mime", "Unknown")
            path = media_info.get("path", "")
            checksum = media_info.get("checksum", "")

            result = f"## Media File: {gramps_id}\n\n"
            result += f"**Description:** {desc}\n"
            result += f"**MIME Type:** {mime}\n"
            result += f"**Path:** {path}\n"
            result += f"**Handle:** `{params.handle}`\n"
            if checksum:
                result += f"**Checksum:** {checksum}\n"

            # Provide download URL hint
            api_url = settings.gramps_api_url
            result += f"\n**File URL:** `{api_url}/api/trees/{tree_id}/media/{params.handle}/file`\n"

            return [TextContent(type="text", text=result)]

        finally:
            await client.close()
    except Exception as e:
        return _format_error_response(e, "media file info")


async def upload_media_file_tool(arguments) -> List[TextContent]:
    """
    Upload a new media file from the local filesystem.

    Creates a new media object in Gramps with the uploaded file.
    Supports common image formats (jpg, png, gif, etc.), PDFs, and other media.
    """
    from ..models.parameters.media_params import MediaFileUploadParams

    try:
        params = _validate_params(arguments, MediaFileUploadParams)
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Validate file exists
        if not os.path.isfile(params.file_path):
            return [
                TextContent(
                    type="text",
                    text=f"Error: File not found: {params.file_path}",
                )
            ]

        # Read file content
        with open(params.file_path, "rb") as f:
            file_content = f.read()

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(params.file_path)
        if not mime_type:
            # Default to binary if unknown
            mime_type = "application/octet-stream"

        # Get file size for reporting
        file_size = len(file_content)
        file_name = os.path.basename(params.file_path)

        client = GrampsWebAPIClient()
        try:
            result = await client.upload_media_file(
                file_content=file_content,
                mime_type=mime_type,
                tree_id=tree_id,
            )

            # Extract created media info
            if isinstance(result, list) and result:
                media_data = result[0].get("new", result[0])
            else:
                media_data = result

            handle = media_data.get("handle", "N/A")
            gramps_id = media_data.get("gramps_id", "N/A")
            checksum = media_data.get("checksum", "")

            response = f"## Media File Uploaded Successfully\n\n"
            response += f"**File:** {file_name}\n"
            response += f"**Size:** {file_size:,} bytes\n"
            response += f"**MIME Type:** {mime_type}\n"
            response += f"**Gramps ID:** {gramps_id}\n"
            response += f"**Handle:** `{handle}`\n"
            if checksum:
                response += f"**Checksum:** {checksum}\n"

            if params.description:
                response += f"\nNote: To add a description, use `create_media` with handle `{handle}`"

            return [TextContent(type="text", text=response)]

        finally:
            await client.close()
    except Exception as e:
        return _format_error_response(e, "media file upload")


async def update_media_file_tool(arguments) -> List[TextContent]:
    """
    Update an existing media object's file from the local filesystem.

    Replaces the file content of an existing media object.
    The media object must already exist (use upload_media_file_tool to create new).
    """
    from ..models.parameters.media_params import MediaFileUpdateParams

    try:
        params = _validate_params(arguments, MediaFileUpdateParams)
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Validate file exists
        if not os.path.isfile(params.file_path):
            return [
                TextContent(
                    type="text",
                    text=f"Error: File not found: {params.file_path}",
                )
            ]

        # Read file content
        with open(params.file_path, "rb") as f:
            file_content = f.read()

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(params.file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        file_size = len(file_content)
        file_name = os.path.basename(params.file_path)

        client = GrampsWebAPIClient()
        try:
            result = await client.update_media_file(
                handle=params.handle,
                file_content=file_content,
                mime_type=mime_type,
                tree_id=tree_id,
            )

            # Extract updated media info
            if isinstance(result, list) and result:
                media_data = result[0].get("new", result[0])
            else:
                media_data = result

            gramps_id = media_data.get("gramps_id", "N/A")
            checksum = media_data.get("checksum", "")

            response = f"## Media File Updated Successfully\n\n"
            response += f"**File:** {file_name}\n"
            response += f"**Size:** {file_size:,} bytes\n"
            response += f"**MIME Type:** {mime_type}\n"
            response += f"**Gramps ID:** {gramps_id}\n"
            response += f"**Handle:** `{params.handle}`\n"
            if checksum:
                response += f"**New Checksum:** {checksum}\n"

            return [TextContent(type="text", text=response)]

        finally:
            await client.close()
    except Exception as e:
        return _format_error_response(e, "media file update")
