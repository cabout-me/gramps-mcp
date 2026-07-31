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
Basic search MCP tools for genealogy operations.

This module contains 8 basic search tools for finding people, families, events,
places, sources, citations, media, and full-text search across all entity types.
"""

import functools
import logging
import re
from typing import Callable, Dict, List

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
from ..models.parameters.base_params import BaseGetMultipleParams
from ..models.parameters.citation_params import GetCitationsParams
from ..models.parameters.event_params import EventSearchParams
from ..models.parameters.media_params import MediaSearchParams
from ..models.parameters.note_params import NotesParams
from ..models.parameters.place_params import PlaceSearchParams
from ..models.parameters.repository_params import RepositoriesParams
from ..models.parameters.search_params import SearchParams
from ..models.parameters.source_params import SourceSearchParams

logger = logging.getLogger(__name__)


def with_client(func: Callable) -> Callable:
    """
    Decorator that provides a GrampsWebAPIClient instance and handles cleanup.

    The decorated function will receive 'client' as the first argument.
    Client is automatically closed after function execution.

    Args:
        func: Async function to decorate

    Returns:
        Decorated function with client management
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        client = GrampsWebAPIClient()
        try:
            return await func(client, *args, **kwargs)
        finally:
            await client.close()

    return wrapper


async def format_search_result_by_type(client, item: Dict) -> str:
    """
    Format search result using appropriate handler based on object type.

    Args:
        client: Gramps API client instance
        item (Dict): Search result item containing object_type and object data

    Returns:
        str: Formatted result string using the appropriate handler
    """
    obj_type = item.get("object_type", "").lower()
    obj = item.get("object", {})
    handle = obj.get("handle", "")

    if not handle:
        return f"• **{obj_type.title()} record** (No handle available)\n\n"

    # Get tree_id from settings
    settings = get_settings()
    tree_id = settings.gramps_tree_id

    try:
        if obj_type == "person":
            return await format_person(client, tree_id, handle)
        elif obj_type == "family":
            return await format_family(client, tree_id, handle)
        elif obj_type == "event":
            return await format_event(client, tree_id, handle)
        elif obj_type == "place":
            return await format_place(client, tree_id, handle)
        elif obj_type == "source":
            return await format_source(client, tree_id, handle)
        elif obj_type == "media":
            return await format_media(client, tree_id, handle)
        elif obj_type == "citation":
            return await format_citation(client, tree_id, handle)
        elif obj_type == "note":
            return await format_note(client, tree_id, handle)
        else:
            gramps_id = obj.get("gramps_id", "N/A")
            title = (
                obj.get("title", "")
                or obj.get("desc", "")
                or f"{obj_type.title()} record"
            )
            return f"• **{title}** ({obj_type.title()} - ID: {gramps_id})\n\n"
    except Exception as e:
        logger.debug(f"Error formatting {obj_type} result: {e}")
        gramps_id = obj.get("gramps_id", "N/A")
        return (
            f"• **{obj_type.title()} record** (ID: {gramps_id}) - "
            "Error formatting details\n\n"
        )


async def _search_entities(
    client,
    arguments: Dict,
    params_class,
    api_call: ApiCalls,
    entity_type: str,
    format_handler,
) -> List[TextContent]:
    """
    Generic search function for all entity types.

    Args:
        client: Gramps API client instance
        arguments: Search parameters dictionary
        params_class: Pydantic model class for parameter validation
        api_call: ApiCalls enum value for the API endpoint
        entity_type: Human-readable entity type for error messages
        format_handler: Async function to format individual results

    Returns:
        List of TextContent with formatted search results
    """
    try:
        # Validate parameters
        params = params_class(**arguments)

        # Get tree_id from settings
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Search using unified API client
        response = await client.make_api_call(
            api_call=api_call, params=params, tree_id=tree_id
        )

        # Extract results and count from response
        if isinstance(response, list):
            results = response
            total_count = len(results)
        else:
            results = response.get("data", [])
            total_count = response.get("total_count", len(results))

        # Format results
        if not results:
            formatted_results = f"No {entity_type} found"
        else:
            actual_total = total_count if total_count is not None else len(results)
            displayed_count = len(results)

            if actual_total > displayed_count:
                header = (
                    f"Found {actual_total} {entity_type} "
                    f"(showing {displayed_count}):\n\n"
                )
            else:
                header = f"Found {actual_total} {entity_type}:\n\n"

            formatted_results = header

            # Process each result with the appropriate handler
            results_to_display = (
                results[: params.pagesize] if params.pagesize else results
            )
            for item in results_to_display:
                if not isinstance(item, dict):
                    continue

                # Extract object from search result wrapper if needed
                obj = item.get("object", item)
                handle = obj.get("handle", "")

                if handle:
                    item_formatted = await format_handler(client, tree_id, handle)
                    formatted_results += item_formatted

        return [TextContent(type="text", text=formatted_results)]

    except Exception as e:
        return _format_error_response(e, f"{entity_type} search")


def _format_error_response(error: Exception, operation: str) -> List[TextContent]:
    """Format error into user-friendly MCP response."""
    if isinstance(error, GrampsAPIError):
        error_msg = str(error)
    else:
        error_msg = f"Unexpected error during {operation}: {str(error)}"

    logger.error(f"Tool error in {operation}: {error_msg}")
    return [TextContent(type="text", text=f"Error: {error_msg}")]


# ============================================================================
# Basic Search Tools (8 tools)
# ============================================================================


@with_client
async def find_person_tool(client, arguments: Dict) -> List[TextContent]:
    """
    Search for people by name, ID, or other criteria.

    Returns limited info: name, birth/death dates and places.
    """
    return await _search_entities(
        client,
        arguments,
        BaseGetMultipleParams,
        ApiCalls.GET_PEOPLE,
        "people",
        format_person,
    )


@with_client
async def find_family_tool(client, arguments: Dict) -> List[TextContent]:
    """
    Search for families (family units).

    Returns limited info: family members' names, marriage date/place.
    """
    return await _search_entities(
        client,
        arguments,
        BaseGetMultipleParams,
        ApiCalls.GET_FAMILIES,
        "families",
        format_family,
    )


@with_client
async def find_event_tool(client, arguments: Dict) -> List[TextContent]:
    """
    Search for life events (births, deaths, marriages).
    """
    return await _search_entities(
        client,
        arguments,
        EventSearchParams,
        ApiCalls.GET_EVENTS,
        "events",
        format_event,
    )


@with_client
async def find_place_tool(client, arguments: Dict) -> List[TextContent]:
    """
    Find geographic locations and places.
    """
    return await _search_entities(
        client,
        arguments,
        PlaceSearchParams,
        ApiCalls.GET_PLACES,
        "places",
        format_place,
    )


@with_client
async def find_source_tool(client, arguments: Dict) -> List[TextContent]:
    """
    Search for source materials and documents.
    """
    return await _search_entities(
        client,
        arguments,
        SourceSearchParams,
        ApiCalls.GET_SOURCES,
        "sources",
        format_source,
    )


@with_client
async def find_repository_tool(client, arguments: Dict) -> List[TextContent]:
    """
    Search for repositories (archives, libraries, churches, etc.).
    """
    return await _search_entities(
        client,
        arguments,
        RepositoriesParams,
        ApiCalls.GET_REPOSITORIES,
        "repositories",
        format_repository,
    )


@with_client
async def find_media_tool(client, arguments: Dict) -> List[TextContent]:
    """
    Find photos, documents, and media files.
    """
    return await _search_entities(
        client,
        arguments,
        MediaSearchParams,
        ApiCalls.GET_MEDIA,
        "media files",
        format_media,
    )


@with_client
async def find_citation_tool(client, arguments: Dict) -> List[TextContent]:
    """
    Search for citations and references, showing source details, URLs, and
    repository info.
    """
    return await _search_entities(
        client,
        arguments,
        GetCitationsParams,
        ApiCalls.GET_CITATIONS,
        "citations",
        format_citation,
    )


# Fields on a note object that client-side note filtering understands.
# "text" maps to the StyledText string payload.
def _note_field_value(note: Dict, field: str):
    """Return the comparable value of a note field for client-side filtering."""
    if field in ("text", "text.string"):
        text = note.get("text")
        if isinstance(text, dict):
            return text.get("string", "")
        return text or ""
    return note.get(field)


def _parse_gql_predicates(gql):
    """Parse a small, safe subset of GQL into (field, op, value) predicates.

    Supported forms (joined by ``and``):
        field = "value"    field == "value"    field != "value"
        "substr" in field

    Returns a list of predicates (empty list means "match everything"), or
    ``None`` if any part of the query cannot be parsed (caller should then
    tell the user the filter is unsupported rather than return wrong results).
    """
    if not gql or not gql.strip():
        return []

    predicates = []
    for part in re.split(r"\s+and\s+", gql.strip(), flags=re.IGNORECASE):
        part = part.strip()
        eq = re.match(r'^(\w+(?:\.\w+)?)\s*(==|=|!=)\s*"([^"]*)"$', part)
        if eq:
            predicates.append((eq.group(1), eq.group(2), eq.group(3)))
            continue
        contains = re.match(
            r'^"([^"]*)"\s+in\s+(\w+(?:\.\w+)?)$', part, flags=re.IGNORECASE
        )
        if contains:
            predicates.append((contains.group(2), "contains", contains.group(1)))
            continue
        return None  # unparseable predicate
    return predicates


def _note_matches(note: Dict, predicates) -> bool:
    """Evaluate parsed predicates against a single note object."""
    for field, op, value in predicates:
        actual = _note_field_value(note, field)
        if op in ("=", "=="):
            if str(actual) != value:
                return False
        elif op == "!=":
            if str(actual) == value:
                return False
        elif op == "contains":
            if value.lower() not in str(actual or "").lower():
                return False
    return True


async def _fetch_all_notes(client, tree_id: str, cap: int = 5000) -> List[Dict]:
    """Fetch all notes WITHOUT a gql filter.

    This backend's /notes endpoint returns HTTP 500 for any ``gql`` query (a
    server-side bug in its GQL engine; other entity types are unaffected).
    Fetching without ``gql`` works, so we page through all notes and filter
    client-side. Paging is capped to avoid unbounded fetches.
    """
    notes: List[Dict] = []
    page = 1
    page_size = 200
    while len(notes) < cap:
        response = await client.make_api_call(
            api_call=ApiCalls.GET_NOTES,
            params=NotesParams(page=page, pagesize=page_size),
            tree_id=tree_id,
        )
        batch = response if isinstance(response, list) else response.get("data", [])
        if not batch:
            break
        notes.extend(batch)
        if len(batch) < page_size:
            break
        page += 1
    return notes


@with_client
async def find_note_tool(client, arguments: Dict) -> List[TextContent]:
    """
    Search for notes and research notes.

    Works around a grampsweb backend bug: any ``gql`` query against the /notes
    endpoint returns HTTP 500. Instead of sending ``gql``, this fetches notes
    unfiltered and applies a supported subset of GQL client-side. See
    ``_parse_gql_predicates`` for the supported syntax.
    """
    try:
        gql = arguments.get("gql")
        pagesize = arguments.get("pagesize")

        predicates = _parse_gql_predicates(gql)
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        if predicates is None:
            return [
                TextContent(
                    type="text",
                    text=(
                        f"Note search could not apply the filter {gql!r}. "
                        "This backend cannot run GQL against notes, so note "
                        "search supports a subset applied locally: "
                        'field =/==/!= "value" and "substr" in field, '
                        "combined with `and`."
                    ),
                )
            ]

        all_notes = await _fetch_all_notes(client, tree_id)
        matched = [n for n in all_notes if _note_matches(n, predicates)]
        total_count = len(matched)

        if pagesize:
            matched = matched[:pagesize]

        if not matched:
            formatted_results = "No notes found"
        else:
            if total_count > len(matched):
                header = f"Found {total_count} notes (showing {len(matched)}):\n\n"
            else:
                header = f"Found {total_count} notes:\n\n"
            formatted_results = header
            for note in matched:
                handle = note.get("handle", "")
                if handle:
                    formatted_results += await format_note(client, tree_id, handle)

        return [TextContent(type="text", text=formatted_results)]

    except Exception as e:
        return _format_error_response(e, "notes search")


async def find_type_tool(arguments: Dict) -> List[TextContent]:
    """Universal type-based search tool."""
    entity_type = arguments.get("type")
    gql = arguments.get("gql")
    max_results = arguments.get("max_results", 20)

    # Get the string value from the enum if needed
    entity_type_str = (
        entity_type.value if hasattr(entity_type, "value") else entity_type
    )

    # Convert to parameters expected by existing tools
    params = {"gql": gql, "pagesize": max_results}

    # Call the existing tool function directly
    tool_name = f"find_{entity_type_str}_tool"
    if tool_name in globals():
        return await globals()[tool_name](params)
    else:
        return [
            TextContent(type="text", text=f"Entity type '{entity_type}' not supported")
        ]


@with_client
async def find_anything_tool(client, arguments: Dict) -> List[TextContent]:
    """
    Full-text search across all entity types.
    """
    try:
        # Validate parameters
        params = SearchParams(**arguments)

        # Get tree_id from settings
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Search using unified API client with headers for total count
        response, headers = await client.make_api_call(
            api_call=ApiCalls.GET_SEARCH,
            params=params,
            tree_id=tree_id,
            with_headers=True,
        )

        # Extract results and count from response and headers
        if isinstance(response, list):
            results = response
        else:
            results = response.get("data", [])

        total_count = int(headers.get("x-total-count", len(results)))

        if not results:
            formatted_results = f"No records found matching '{params.query}'"
        else:
            actual_total = total_count if total_count is not None else len(results)
            displayed_count = len(results)

            if actual_total > displayed_count:
                header = (
                    f"Found {actual_total} records matching '{params.query}' "
                    f"(showing {displayed_count}):\n\n"
                )
            else:
                header = f"Found {actual_total} records matching '{params.query}':\n\n"

            formatted_results = header

            # Process each result with type-specific handler
            results_to_display = (
                results[: params.pagesize] if params.pagesize else results
            )
            for item in results_to_display:
                if not isinstance(item, dict):
                    continue

                result_formatted = await format_search_result_by_type(client, item)
                formatted_results += result_formatted

        return [TextContent(type="text", text=formatted_results)]

    except Exception as e:
        return _format_error_response(e, "full-text search")
