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
Analysis MCP tools for genealogy operations.

This module contains 4 analysis tools for genealogy research including
tree statistics, ancestor/descendant discovery, and recent changes tracking.
"""

import asyncio
import json
import logging
from typing import Dict, List

from mcp.types import TextContent

from ..client import GrampsAPIError, GrampsWebAPIClient
from ..config import get_settings
from ..models.api_calls import ApiCalls
from ..models.parameters.reports_params import ReportFileParams
from ..utils import get_gramps_id_from_handle, html_to_markdown
from .search_basic import with_client

logger = logging.getLogger(__name__)


def _get_arg(arguments, key, default=None):
    """Get argument value from either dict or BaseModel."""
    from pydantic import BaseModel

    if isinstance(arguments, BaseModel):
        return getattr(arguments, key, default)
    return arguments.get(key, default)


def _format_error_response(error: Exception, operation: str) -> List[TextContent]:
    """Format error into user-friendly MCP response."""
    if isinstance(error, GrampsAPIError):
        error_msg = str(error)
    else:
        error_msg = f"Unexpected error during {operation}: {str(error)}"

    logger.error(f"Tool error in {operation}: {error_msg}")
    return [TextContent(type="text", text=f"Error: {error_msg}")]


async def _format_recent_changes(
    transactions: List[Dict], client: GrampsWebAPIClient, tree_id: str
) -> str:
    """Format transaction history results."""
    if not transactions:
        return "No recent changes found."

    result = f"Found {len(transactions)} recent changes:\n\n"

    for transaction in transactions:
        # Extract transaction information
        timestamp = transaction.get("timestamp", "Unknown time")
        description = transaction.get("description", "Transaction")

        # Convert timestamp to human readable format
        if isinstance(timestamp, (int, float)):
            from datetime import datetime

            formatted_time = datetime.fromtimestamp(timestamp).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        else:
            formatted_time = str(timestamp)

        # User information
        connection = transaction.get("connection", {})
        user = connection.get("user", {})
        user_name = user.get("name", "Unknown") if user else "Unknown"

        # Changes in this transaction
        changes = transaction.get("changes", [])
        change_count = len(changes)

        result += f"• **{description}**\n"
        result += f"  Time: {formatted_time}\n"
        result += f"  User: {user_name}\n"

        if changes:
            result += "  Objects changed:\n"
            for change in changes[:3]:  # Show first 3 changes
                obj_class = change.get("obj_class", "Unknown")
                obj_handle = change.get("obj_handle", "N/A")

                # Get gramps_id from handle using utility function
                gramps_id = await get_gramps_id_from_handle(
                    client, obj_class, obj_handle, tree_id
                )
                result += f"    - {obj_class}: {gramps_id}\n"
            if len(changes) > 3:
                result += f"    - ... and {len(changes) - 3} more\n"
        else:
            result += f"  Changes: {change_count} objects modified\n"

        result += "\n"

    return result


async def _wait_for_task_completion(
    client: GrampsWebAPIClient, task_id: str, tree_id: str, timeout: int = 60
) -> Dict:
    """
    Wait for an async task to complete by polling its status.

    Args:
        client: Gramps API client
        task_id: Task ID to poll
        tree_id: Tree ID (unused for tasks, but kept for compatibility)
        timeout: Maximum wait time in seconds

    Returns:
        Dict: Completed task result containing filename

    Raises:
        GrampsAPIError: If task fails or times out
    """
    start_time = asyncio.get_event_loop().time()
    sleep_interval = 2  # Start with 2 second intervals
    max_sleep = 10  # Maximum sleep interval

    while True:
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > timeout:
            raise GrampsAPIError(f"Task {task_id} timed out after {timeout} seconds")

        try:
            # Poll task status using direct HTTP call
            # (tasks are global, not tree-specific)
            task_url = f"{client.base_url}/tasks/{task_id}"
            task_status = await client._make_request("GET", task_url)

            logger.debug(f"Task {task_id} status: {task_status}")

            # Check if task is complete (use 'state' field, not 'status')
            state = task_status.get("state", "").upper()
            if state == "SUCCESS":
                # Task completed successfully, return the result_object
                result = task_status.get("result_object") or task_status.get("result")
                if result:
                    return result
                else:
                    logger.warning(
                        f"Task {task_id} succeeded but no result found: {task_status}"
                    )
                    return task_status
            elif state == "FAILURE" or state == "FAILED":
                error_msg = task_status.get("info", "Task failed")
                raise GrampsAPIError(f"Task {task_id} failed: {error_msg}")

            # Task still running, wait before checking again
            logger.debug(
                f"Task {task_id} still running (state: {state}), "
                f"waiting {sleep_interval}s..."
            )
            await asyncio.sleep(sleep_interval)

            # Exponential backoff, but cap at max_sleep
            sleep_interval = min(sleep_interval * 1.5, max_sleep)

        except Exception as e:
            if isinstance(e, GrampsAPIError):
                raise
            raise GrampsAPIError(f"Error polling task {task_id}: {str(e)}")


# ============================================================================
# Analysis Tools (4 tools)
# ============================================================================


@with_client
async def get_descendants_tool(client, arguments) -> List[TextContent]:
    """
    Find all descendants of a person.
    """
    try:
        # Extract arguments (handles both dict and BaseModel)
        gramps_id = _get_arg(arguments, "gramps_id")
        max_generations = _get_arg(arguments, "max_generations")

        if not gramps_id:
            raise ValueError("gramps_id is required")

        # Get tree_id from settings
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Prepare report options with default of 5 generations
        report_options = {"pid": gramps_id, "off": "html"}
        # Use provided max_generations or default to 5
        generations = max_generations if max_generations is not None else 5
        report_options["gen"] = str(generations)

        # Generate descendant report using unified API
        generate_params = ReportFileParams(options=json.dumps(report_options))

        report_result = await client.make_api_call(
            api_call=ApiCalls.POST_REPORT_FILE,
            params=generate_params,
            tree_id=tree_id,
            report_id="descend_report",
        )

        # Extract filename from response to download processed report
        logger.debug(f"Descendants report generation response: {report_result}")

        # Handle both sync (direct filename) and async (task) responses
        filename = report_result.get("file_name")
        if not filename:
            # Check if this is an async task response
            task_info = report_result.get("task")
            if task_info and "id" in task_info:
                task_id = task_info["id"]
                logger.debug(
                    f"Descendants report is running as async task {task_id}, "
                    "waiting for completion..."
                )

                # Wait for task completion
                completed_task = await _wait_for_task_completion(
                    client, task_id, tree_id
                )
                filename = completed_task.get("file_name")

                if not filename:
                    raise GrampsAPIError(
                        f"Task completed but filename not found in result. "
                        f"Result: {completed_task}"
                    )
            else:
                raise GrampsAPIError(
                    f"Report generated but filename not found in response. "
                    f"Response: {report_result}"
                )

        # Download the processed report content
        download_params = ReportFileParams(
            options=None  # No options needed for download
        )

        report_response = await client.make_api_call(
            api_call=ApiCalls.GET_REPORT_PROCESSED,
            params=download_params,
            tree_id=tree_id,
            report_id="descend_report",
            filename=filename,
        )

        # Extract HTML content from response
        if isinstance(report_response, dict) and "raw_content" in report_response:
            report_content = report_response["raw_content"]
        else:
            report_content = str(report_response)

        # Convert HTML to Markdown
        markdown_content = html_to_markdown(report_content)

        return [TextContent(type="text", text=markdown_content)]

    except Exception as e:
        return _format_error_response(e, "descendants search")


@with_client
async def get_ancestors_tool(client, arguments) -> List[TextContent]:
    """
    Find all ancestors of a person.
    """
    try:
        # Extract arguments (handles both dict and BaseModel)
        gramps_id = _get_arg(arguments, "gramps_id")
        max_generations = _get_arg(arguments, "max_generations")

        if not gramps_id:
            raise ValueError("gramps_id is required")

        # Get tree_id from settings
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Prepare report options with default of 5 generations
        report_options = {"pid": gramps_id, "off": "html"}
        # Use provided max_generations or default to 5
        generations = max_generations if max_generations is not None else 5
        report_options["maxgen"] = str(generations)

        # Generate ancestor report using unified API
        generate_params = ReportFileParams(options=json.dumps(report_options))

        report_result = await client.make_api_call(
            api_call=ApiCalls.POST_REPORT_FILE,
            params=generate_params,
            tree_id=tree_id,
            report_id="ancestor_report",
        )

        # Extract filename from response to download processed report
        logger.debug(f"Ancestors report generation response: {report_result}")

        # Handle both sync (direct filename) and async (task) responses
        filename = report_result.get("file_name")
        if not filename:
            # Check if this is an async task response
            task_info = report_result.get("task")
            if task_info and "id" in task_info:
                task_id = task_info["id"]
                logger.debug(
                    f"Ancestors report is running as async task {task_id}, "
                    "waiting for completion..."
                )

                # Wait for task completion
                completed_task = await _wait_for_task_completion(
                    client, task_id, tree_id
                )
                filename = completed_task.get("file_name")

                if not filename:
                    raise GrampsAPIError(
                        f"Task completed but filename not found in result. "
                        f"Result: {completed_task}"
                    )
            else:
                raise GrampsAPIError(
                    f"Report generated but filename not found in response. "
                    f"Response: {report_result}"
                )

        # Download the processed report content
        download_params = ReportFileParams(
            options=None  # No options needed for download
        )

        report_response = await client.make_api_call(
            api_call=ApiCalls.GET_REPORT_PROCESSED,
            params=download_params,
            tree_id=tree_id,
            report_id="ancestor_report",
            filename=filename,
        )

        # Extract HTML content from response
        if isinstance(report_response, dict) and "raw_content" in report_response:
            report_content = report_response["raw_content"]
        else:
            report_content = str(report_response)

        # Convert HTML to Markdown
        markdown_content = html_to_markdown(report_content)

        return [TextContent(type="text", text=markdown_content)]

    except Exception as e:
        return _format_error_response(e, "ancestors search")


@with_client
async def get_recent_changes_tool(client, arguments: Dict) -> List[TextContent]:
    """
    Get recent changes/modifications to the family tree.
    """
    try:
        # Import and validate parameters
        from ..models.parameters.transactions_params import TransactionHistoryParams

        # Validate parameters and ensure we get most recent changes first
        if not arguments:
            arguments = {}
        arguments["sort"] = "-id"
        params = TransactionHistoryParams(**arguments)

        # Get tree_id from settings
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Get recent transaction history using unified API
        changes = await client.make_api_call(
            api_call=ApiCalls.GET_TRANSACTIONS_HISTORY, params=params, tree_id=tree_id
        )

        formatted_changes = await _format_recent_changes(changes, client, tree_id)
        return [TextContent(type="text", text=formatted_changes)]

    except Exception as e:
        return _format_error_response(e, "recent changes retrieval")


def _format_tree_info(tree_info: Dict) -> str:
    """Format tree information for display."""
    tree_id = tree_info.get("id", "N/A")
    name = tree_info.get("name", "Unnamed Tree")
    description = tree_info.get("description", "")

    result = f"# Family Tree: {name}\n\n"
    result += f"**Tree ID:** `{tree_id}`\n"
    if description:
        result += f"**Description:** {description}\n"
    result += "\n"

    # Statistics from usage fields
    usage_people = tree_info.get("usage_people")
    usage_media = tree_info.get("usage_media")

    result += "## Statistics\n\n"

    if usage_people is not None or usage_media is not None:
        if usage_people is not None:
            result += f"• **People:** {usage_people:,}\n"
        if usage_media is not None:
            usage_media_mb = usage_media / (1024 * 1024)
            result += f"• **Media Storage:** {usage_media_mb:.2f} MB\n"
        result += "\n"
    else:
        result += "Statistics not available\n\n"

    return result


@with_client
async def get_relations_tool(client, arguments) -> List[TextContent]:
    """
    Find the relationship between two people.
    """
    try:
        handle1 = _get_arg(arguments, "handle1")
        handle2 = _get_arg(arguments, "handle2")

        if not handle1 or not handle2:
            raise ValueError("Both handle1 and handle2 are required")

        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Get relationship using the API
        relations = await client.make_api_call(
            api_call=ApiCalls.GET_RELATIONS,
            params=None,
            tree_id=tree_id,
            handle1=handle1,
            handle2=handle2,
        )

        if not relations:
            return [TextContent(type="text", text="No relationship found between these two people.")]

        # Format the relationship result
        # API returns: {"distance_common_origin": N, "distance_common_other": M, "relationship_string": "..."}
        result = "## Relationship Found\n\n"

        if isinstance(relations, dict):
            relationship = relations.get("relationship_string", "Unknown")
            dist_origin = relations.get("distance_common_origin")
            dist_other = relations.get("distance_common_other")

            result += f"**Relationship:** {relationship}\n"

            if dist_origin is not None and dist_other is not None:
                total_distance = dist_origin + dist_other
                result += f"**Total Distance:** {total_distance} generations\n"
                result += f"  - From person 1 to common ancestor: {dist_origin}\n"
                result += f"  - From common ancestor to person 2: {dist_other}\n"
        else:
            result += str(relations)

        return [TextContent(type="text", text=result)]

    except Exception as e:
        return _format_error_response(e, "relationship lookup")


@with_client
async def get_tree_info_tool(client, _arguments) -> List[TextContent]:
    """
    Get information about a specific tree including statistics.

    Returns counts of people, families, events, etc.
    """
    try:
        # Get tree_id from settings
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Get tree info using unified API
        tree_info = await client.make_api_call(
            api_call=ApiCalls.GET_TREE, params=None, tree_id=tree_id
        )

        formatted_info = _format_tree_info(tree_info)
        return [TextContent(type="text", text=formatted_info)]

    except Exception as e:
        return _format_error_response(e, "tree information retrieval")


# ============================================================================
# Living Status Tools
# ============================================================================


@with_client
async def get_living_tool(client, arguments) -> List[TextContent]:
    """
    Check if a person is considered living (for privacy purposes).
    """
    try:
        handle = _get_arg(arguments, "handle")

        if not handle:
            raise ValueError("handle is required")

        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Get living status
        result = await client.make_api_call(
            api_call=ApiCalls.GET_LIVING,
            params=None,
            tree_id=tree_id,
            handle=handle,
        )

        # Format response
        is_living = result.get("living", False) if isinstance(result, dict) else result
        status = "LIVING" if is_living else "DECEASED"

        return [
            TextContent(
                type="text",
                text=f"**Living Status:** {status}\n\nHandle: `{handle}`",
            )
        ]

    except Exception as e:
        return _format_error_response(e, "living status check")


# ============================================================================
# Facts Tools
# ============================================================================


@with_client
async def get_facts_tool(client, arguments) -> List[TextContent]:
    """
    Get computed facts and statistics about the family tree.
    """
    try:
        from ..models.parameters.facts_params import FactsParams

        # Extract only explicitly provided arguments (not defaults)
        # to avoid sending extra params the API rejects
        if isinstance(arguments, FactsParams):
            # Get only user-provided values
            params_dict = arguments.model_dump(exclude_unset=True)
        elif isinstance(arguments, dict):
            params_dict = {k: v for k, v in arguments.items() if v is not None}
        else:
            params_dict = {}

        # Only create params if there are explicit values to send
        params = FactsParams(**params_dict) if params_dict else None

        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Get facts
        facts = await client.make_api_call(
            api_call=ApiCalls.GET_FACTS,
            params=params,
            tree_id=tree_id,
        )

        # Format response
        if not facts:
            return [TextContent(type="text", text="No facts available.")]

        result = "# Tree Facts\n\n"

        if isinstance(facts, dict):
            for key, value in facts.items():
                if isinstance(value, dict):
                    result += f"## {key.replace('_', ' ').title()}\n"
                    for sub_key, sub_value in value.items():
                        result += f"- **{sub_key}:** {sub_value}\n"
                    result += "\n"
                elif isinstance(value, list):
                    result += f"## {key.replace('_', ' ').title()}\n"
                    for item in value[:10]:  # Limit to first 10
                        result += f"- {item}\n"
                    result += "\n"
                else:
                    result += f"- **{key.replace('_', ' ').title()}:** {value}\n"
        else:
            result += str(facts)

        return [TextContent(type="text", text=result)]

    except Exception as e:
        return _format_error_response(e, "facts retrieval")


# ============================================================================
# Relations All Tool
# ============================================================================


@with_client
async def get_relations_all_tool(client, arguments) -> List[TextContent]:
    """
    Find ALL possible relationship paths between two people.
    """
    try:
        handle1 = _get_arg(arguments, "handle1")
        handle2 = _get_arg(arguments, "handle2")

        if not handle1 or not handle2:
            raise ValueError("Both handle1 and handle2 are required")

        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Get all relationships
        relations = await client.make_api_call(
            api_call=ApiCalls.GET_RELATIONS_ALL,
            params=None,
            tree_id=tree_id,
            handle1=handle1,
            handle2=handle2,
        )

        if not relations:
            return [
                TextContent(
                    type="text",
                    text="No relationships found between these two people.",
                )
            ]

        # Format all relationships
        result = "## All Relationship Paths\n\n"

        if isinstance(relations, list):
            for i, rel in enumerate(relations, 1):
                relationship = rel.get("relationship_string", "Unknown")
                dist_origin = rel.get("distance_common_origin")
                dist_other = rel.get("distance_common_other")

                result += f"**Path {i}:** {relationship}\n"
                if dist_origin is not None and dist_other is not None:
                    result += f"  - Distance: {dist_origin + dist_other} generations\n"
                result += "\n"
        else:
            result += str(relations)

        return [TextContent(type="text", text=result)]

    except Exception as e:
        return _format_error_response(e, "all relationships lookup")


# ============================================================================
# Timeline Tools
# ============================================================================


@with_client
async def get_people_timeline_tool(client, arguments) -> List[TextContent]:
    """
    Get a timeline of events for a group of people.
    """
    try:
        from ..models.parameters.timeline_params import PeopleTimelineParams

        # Extract only explicitly provided arguments (not defaults)
        # to avoid sending extra params the API rejects
        if isinstance(arguments, PeopleTimelineParams):
            params_dict = arguments.model_dump(exclude_unset=True)
        elif isinstance(arguments, dict):
            params_dict = {k: v for k, v in arguments.items() if v is not None}
        else:
            params_dict = {}

        # Only create params if there are explicit values to send
        params = PeopleTimelineParams(**params_dict) if params_dict else None

        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Get timeline
        timeline = await client.make_api_call(
            api_call=ApiCalls.GET_TIMELINES_PEOPLE,
            params=params,
            tree_id=tree_id,
        )

        if not timeline:
            return [TextContent(type="text", text="No timeline events found.")]

        # Format timeline
        result = "# People Timeline\n\n"

        events = timeline if isinstance(timeline, list) else timeline.get("data", [])
        for event in events[:50]:  # Limit output
            # Date can be a string or dict depending on API version
            date = event.get("date", "Unknown date")
            if isinstance(date, dict):
                date_str = date.get("sortval", date.get("text", "Unknown date"))
            else:
                date_str = str(date) if date else "Unknown date"

            event_type = event.get("type", event.get("label", "Event"))
            description = event.get("description", "")
            age = event.get("age", "")

            # Person info - the person field is a dict with name_display, etc.
            person = event.get("person", {})
            if isinstance(person, dict):
                person_name = person.get("name_display", person.get("name", ""))
            else:
                person_name = ""

            result += f"- **{date_str}** - {event_type}"
            if description:
                result += f": {description}"
            if person_name:
                result += f" ({person_name})"
            if age:
                result += f" [age: {age}]"
            result += "\n"

        return [TextContent(type="text", text=result)]

    except Exception as e:
        return _format_error_response(e, "people timeline retrieval")


@with_client
async def get_families_timeline_tool(client, arguments) -> List[TextContent]:
    """
    Get a timeline of events for a group of families.
    """
    try:
        from ..models.parameters.timeline_params import FamiliesTimelineParams

        # Extract only explicitly provided arguments (not defaults)
        # to avoid sending extra params the API rejects
        if isinstance(arguments, FamiliesTimelineParams):
            params_dict = arguments.model_dump(exclude_unset=True)
        elif isinstance(arguments, dict):
            params_dict = {k: v for k, v in arguments.items() if v is not None}
        else:
            params_dict = {}

        # Only create params if there are explicit values to send
        params = FamiliesTimelineParams(**params_dict) if params_dict else None

        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Get timeline
        timeline = await client.make_api_call(
            api_call=ApiCalls.GET_TIMELINES_FAMILIES,
            params=params,
            tree_id=tree_id,
        )

        if not timeline:
            return [TextContent(type="text", text="No family timeline events found.")]

        # Format timeline
        result = "# Families Timeline\n\n"

        events = timeline if isinstance(timeline, list) else timeline.get("data", [])
        for event in events[:50]:  # Limit output
            # Date can be a string or dict depending on API version
            date = event.get("date", "Unknown date")
            if isinstance(date, dict):
                date_str = date.get("sortval", date.get("text", "Unknown date"))
            else:
                date_str = str(date) if date else "Unknown date"

            event_type = event.get("type", event.get("label", "Event"))
            description = event.get("description", "")
            age = event.get("age", "")

            # Person info if available
            person = event.get("person", {})
            if isinstance(person, dict):
                person_name = person.get("name_display", person.get("name", ""))
            else:
                person_name = ""

            result += f"- **{date_str}** - {event_type}"
            if description:
                result += f": {description}"
            if person_name:
                result += f" ({person_name})"
            if age:
                result += f" [age: {age}]"
            result += "\n"

        return [TextContent(type="text", text=result)]

    except Exception as e:
        return _format_error_response(e, "families timeline retrieval")


# ============================================================================
# Event Span Tool
# ============================================================================


@with_client
async def get_event_span_tool(client, arguments) -> List[TextContent]:
    """
    Calculate the time span between two events.

    Useful for questions like "How old was X when Y happened?" or
    "How long between marriage and first child?"
    """
    try:
        handle1 = _get_arg(arguments, "handle1")
        handle2 = _get_arg(arguments, "handle2")
        precision = _get_arg(arguments, "precision", 2)
        as_age = _get_arg(arguments, "as_age", True)

        if not handle1 or not handle2:
            raise ValueError("Both handle1 and handle2 are required")

        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Build query params - only include if explicitly set to non-default values
        params = {}
        if precision is not None and precision != 2:
            params["precision"] = precision
        if as_age is not None and not as_age:
            params["as_age"] = as_age

        # Get event span
        result = await client.make_api_call(
            api_call=ApiCalls.GET_EVENT_SPAN,
            params=params if params else None,
            tree_id=tree_id,
            handle1=handle1,
            handle2=handle2,
        )

        span = result.get("span", "unknown") if isinstance(result, dict) else "unknown"

        response = f"## Time Span Between Events\n\n"
        response += f"**Event 1:** `{handle1}`\n"
        response += f"**Event 2:** `{handle2}`\n"
        response += f"**Span:** {span}\n"

        if span == "unknown":
            response += "\n*Note: Span could not be calculated. This usually means one or both events don't have complete dates.*"

        return [TextContent(type="text", text=response)]

    except Exception as e:
        return _format_error_response(e, "event span calculation")


# ============================================================================
# Types Reference Tool
# ============================================================================


@with_client
async def get_types_tool(client, arguments) -> List[TextContent]:
    """
    Get all valid type values for Gramps records.

    Returns valid values for event types, name types, place types,
    note types, and more. Useful as a reference when creating records.
    """
    try:
        settings = get_settings()
        tree_id = settings.gramps_tree_id

        # Get default types
        result = await client.make_api_call(
            api_call=ApiCalls.GET_TYPES_DEFAULT,
            params=None,
            tree_id=tree_id,
        )

        if not result:
            return [TextContent(type="text", text="No type information available.")]

        response = "# Gramps Type Reference\n\n"
        response += "Valid values for each record type:\n\n"

        # Format each type category
        type_categories = [
            ("event_types", "Event Types"),
            ("name_types", "Name Types"),
            ("place_types", "Place Types"),
            ("note_types", "Note Types"),
            ("family_relation_types", "Family Relation Types"),
            ("gender_types", "Gender Types"),
            ("repository_types", "Repository Types"),
            ("source_media_types", "Source Media Types"),
            ("name_origin_types", "Name Origin Types"),
            ("event_role_types", "Event Role Types"),
            ("child_reference_types", "Child Reference Types"),
            ("attribute_types", "Attribute Types"),
            ("url_types", "URL Types"),
        ]

        for key, label in type_categories:
            if key in result:
                values = result[key]
                response += f"## {label}\n"
                # Format as comma-separated list, max 8 per line
                for i in range(0, len(values), 8):
                    chunk = values[i:i+8]
                    response += ", ".join(chunk) + "\n"
                response += "\n"

        return [TextContent(type="text", text=response)]

    except Exception as e:
        return _format_error_response(e, "types retrieval")
