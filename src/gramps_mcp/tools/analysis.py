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
async def get_descendants_tool(client, arguments: Dict) -> List[TextContent]:
    """
    Find all descendants of a person.
    """
    try:
        # Extract arguments directly
        gramps_id = arguments.get("gramps_id")
        max_generations = arguments.get("max_generations")

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
async def get_ancestors_tool(client, arguments: Dict) -> List[TextContent]:
    """
    Find all ancestors of a person.
    """
    try:
        # Extract arguments directly
        gramps_id = arguments.get("gramps_id")
        max_generations = arguments.get("max_generations")

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
async def get_tree_info_tool(client, _arguments: Dict) -> List[TextContent]:
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
