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
Source data handler for Gramps MCP operations.

Provides clean, direct formatting of source data from handles.
"""

import logging

from ..models.api_calls import ApiCalls

logger = logging.getLogger(__name__)


async def format_source(client, tree_id: str, handle: str) -> str:
    """
    Format source data with title, author, and publication details.

    Args:
        client: Gramps API client instance
        tree_id: Family tree identifier
        handle: Source handle

    Returns:
        Formatted source string with details
    """
    if not handle:
        return "• **Unknown Source**\n  No handle provided\n\n"

    try:
        source_data = await client.make_api_call(
            api_call=ApiCalls.GET_SOURCE, tree_id=tree_id, handle=handle
        )
        if not source_data:
            return f"• **Source {handle}**\n  Source not found\n\n"

        gramps_id = source_data.get("gramps_id", "")
        title = source_data.get("title", "").strip()
        author = source_data.get("author", "").strip()
        pubinfo = source_data.get("pubinfo", "").strip()
        note_list = source_data.get("note_list", [])
        reporef_list = source_data.get("reporef_list", [])
        media_list = source_data.get("media_list", [])

        # First line: Title - gramps_id - [handle]
        first_line = f"{title} - {gramps_id} - [{handle}]"
        result = first_line

        # Second line: author - pub info (if available)
        if author or pubinfo:
            second_line_parts = []
            if author:
                second_line_parts.append(author)
            if pubinfo:
                second_line_parts.append(pubinfo)
            result += f"\n{' - '.join(second_line_parts)}"

        # Repository info: repo name - gramps id
        for reporef in reporef_list:
            if not isinstance(reporef, dict):
                continue
            repo_handle = reporef.get("ref", "")
            if not repo_handle:
                continue

            try:
                repo_data = await client.make_api_call(
                    api_call=ApiCalls.GET_REPOSITORY,
                    tree_id=tree_id,
                    handle=repo_handle,
                )
                if repo_data:
                    repo_name = repo_data.get("name", "").strip()
                    repo_gramps_id = repo_data.get("gramps_id", "")
                    if repo_name and repo_gramps_id:
                        result += f"\n{repo_name} - {repo_gramps_id}"
            except Exception:
                continue

        # Attached media: gramps_id(s)
        if media_list:
            media_ids = []
            for media_ref in media_list:
                if isinstance(media_ref, dict):
                    media_handle = media_ref.get("ref", "")
                    if media_handle:
                        try:
                            media_data = await client.make_api_call(
                                api_call=ApiCalls.GET_MEDIA_ITEM,
                                tree_id=tree_id,
                                handle=media_handle,
                            )
                            if media_data:
                                media_gramps_id = media_data.get("gramps_id", "")
                                if media_gramps_id:
                                    media_ids.append(media_gramps_id)
                        except Exception:
                            continue

            if media_ids:
                result += f"\nAttached media: {', '.join(media_ids)}"

        # Attached notes: gramps_id(s)
        if note_list:
            note_ids = []
            for note_handle in note_list:
                try:
                    note_data = await client.make_api_call(
                        api_call=ApiCalls.GET_NOTE, tree_id=tree_id, handle=note_handle
                    )
                    if note_data:
                        note_gramps_id = note_data.get("gramps_id", "")
                        if note_gramps_id:
                            note_ids.append(note_gramps_id)
                except Exception:
                    continue

            if note_ids:
                result += f"\nAttached notes: {', '.join(note_ids)}"

        return result + "\n\n"

    except Exception as e:
        logger.debug(f"Failed to format source {handle}: {e}")
        return f"• **Source {handle}**\n  Error formatting source: {str(e)}\n\n"
