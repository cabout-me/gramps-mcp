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
Database lifecycle MCP tools.

Provides three tools for managing the active Gramps database connection:

- ``open_database``   — open (or switch to) a database file
- ``close_database``  — release the connection so Gramps Desktop can use it
- ``reload_database`` — re-read the database after Gramps Desktop made changes
"""

import logging
from typing import Dict, List

from mcp.types import TextContent

from ..client import (
    GrampsAPIError,
    close_database,
    list_databases,
    open_database,
)

logger = logging.getLogger(__name__)


def _db_summary(client) -> str:
    """Return a short stats summary for the active database."""
    db = client._db
    return (
        f"  People:       {db.count('person')}\n"
        f"  Families:     {db.count('family')}\n"
        f"  Events:       {db.count('event')}\n"
        f"  Places:       {db.count('place')}\n"
        f"  Sources:      {db.count('source')}\n"
        f"  Citations:    {db.count('citation')}\n"
        f"  Notes:        {db.count('note')}\n"
        f"  Media:        {db.count('media')}\n"
        f"  Repositories: {db.count('repository')}"
    )


async def list_databases_tool(arguments: Dict) -> List[TextContent]:
    """
    List all Gramps databases found on this machine.

    Reads the platform-specific Gramps ``grampsdb`` directory and
    returns the name, backend type, and path for each tree.

    Args:
        arguments: Not used.

    Returns:
        Formatted list of available Gramps databases.
    """
    dbs = list_databases()
    if not dbs:
        return [TextContent(
            type="text",
            text=(
                "No Gramps databases found on this machine.\n"
                "Check that Gramps is installed and has at least one family tree."
            ),
        )]
    lines = [f"Found {len(dbs)} Gramps database(s):\n"]
    for db in dbs:
        mode = "read/write" if db["writable"] else "read-only"
        locked_by = db.get("locked_by", "")
        lock_info = ""
        if "gramps_mcp" in locked_by:
            lock_info = "  🔒 locked by gramps_mcp (this agent)"
        elif locked_by:
            lock_info = f"  🔒 locked by {locked_by} (Gramps Desktop?)"
        lines.append(
            f"  {db['name']!r}  [{db['id']}]\n"
            f"    Backend: {db['backend']}  ({mode}){lock_info}\n"
            f"    Path:    {db['path']}"
        )
    lines.append(
        "\nTo open one, call open_database with its path."
    )
    return [TextContent(type="text", text="\n".join(lines))]


async def open_database_tool(arguments: Dict) -> List[TextContent]:
    """
    Open a Gramps database file, replacing any currently active connection.

    Accepts ``.sqlite`` / ``.db`` files (or directories containing
    ``sqlite.db``) for full read/write access, or ``.gpkg`` / ``.gramps``
    files for read-only access.

    Args:
        arguments: Dict with key ``path`` — absolute path to the database.

    Returns:
        Confirmation message with record counts.
    """
    path = (arguments.get("path") or "").strip()
    if not path:
        return [TextContent(type="text", text="Error: 'path' is required.")]
    try:
        client, locked_by = open_database(path)
        is_sqlite = hasattr(client._db, "_conn")
        mode = "read/write (SQLite)" if is_sqlite else "read-only (XML)"
        lines = [
            f"Database opened in {mode} mode.",
            f"Path: {path}",
        ]
        if locked_by and "gramps_mcp" not in locked_by:
            lines.append(
                f"\n⚠️  Database locked by {locked_by} (Gramps Desktop open?).\n"
                "Opened in READ-ONLY mode — writes are disabled.\n"
                "Close Gramps Desktop and call reload_database to enable writes."
            )
        lines.append(f"\nRecord counts:\n{_db_summary(client)}")
        return [TextContent(type="text", text="\n".join(lines))]
    except GrampsAPIError as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]
    except Exception as exc:
        logger.exception("open_database_tool failed")
        return [TextContent(type="text", text=f"Unexpected error: {exc}")]


async def close_database_tool(arguments: Dict) -> List[TextContent]:
    """
    Close the current database connection and release any file locks.

    Call this before opening the database in Gramps Desktop to avoid
    conflicting SQLite locks.  The path is remembered so
    ``reload_database`` can reopen it afterwards.

    Args:
        arguments: Not used.

    Returns:
        Confirmation message.
    """
    path = close_database()
    if path:
        msg = (
            f"Database closed: {path}\n\n"
            "You can now safely open this database in Gramps Desktop.\n"
            "Call open_database when you are done."
        )
    else:
        msg = "No database was open."
    return [TextContent(type="text", text=msg)]
