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
Unified Gramps Web API client.

This module provides a single client class that uses the unified API call system
for all Gramps Web API operations through the make_api_call method.
"""

import logging
import os
import re
from typing import Dict, Optional, Union
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

from .auth import AuthManager
from .config import get_settings
from .models.api_calls import ApiCalls
from .models.api_mapping import validate_api_call_params

logger = logging.getLogger(__name__)


class GrampsAPIError(Exception):
    """Custom exception for Gramps Web API errors."""

    pass


class GrampsWebAPIClient:
    """Unified async HTTP client for all Gramps Web API operations."""

    def __init__(self):
        """Initialize the unified Gramps Web API client."""
        self.settings = get_settings()
        # Use singleton AuthManager - no new instances created
        self.auth_manager = AuthManager()

        # Construct base API URL
        base_url = str(self.settings.gramps_api_url).rstrip("/")
        if not base_url.endswith("/api"):
            base_url += "/api"
        self.base_url = base_url

    async def close(self):
        """Close the HTTP client and auth manager."""
        await self.auth_manager.close()

    async def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        # Use the auth manager's method to get headers with valid token
        await self.auth_manager.get_token()
        return self.auth_manager.get_headers()

    def _build_url(self, tree_id: str, endpoint: str) -> str:
        """Build complete URL for API endpoint."""
        # The tree_id is handled via authentication token, not URL path
        # Ensure base_url ends with / for proper urljoin behavior
        base = self.base_url.rstrip("/") + "/"
        return urljoin(base, endpoint)

    async def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        retry_auth: bool = True,
        return_headers: bool = False,
    ):
        """Make HTTP request with error handling and auth retry."""
        try:
            headers = await self._get_headers()
            response = await self.auth_manager.client.request(
                method=method, url=url, params=params, json=json_data, headers=headers
            )

            # Handle 401 with token refresh retry
            if response.status_code == 401 and retry_auth:
                logger.info("Got 401, refreshing token and retrying")
                await self.auth_manager.authenticate()
                return await self._make_request(
                    method,
                    url,
                    params,
                    json_data,
                    retry_auth=False,
                    return_headers=return_headers,
                )

            response.raise_for_status()

            # Handle empty responses
            if not response.text.strip():
                if return_headers:
                    return {}, dict(response.headers)
                return {}

            try:
                data = response.json()
                if return_headers:
                    return data, dict(response.headers)
                return data
            except Exception as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                error_response = {
                    "error": "Invalid JSON response",
                    "raw_content": response.text,
                }
                if return_headers:
                    return error_response, dict(response.headers)
                return error_response

        except httpx.HTTPStatusError as e:
            error_msg = self._format_http_error(e)
            raise GrampsAPIError(error_msg) from e
        except httpx.ConnectError as e:
            raise GrampsAPIError(f"Cannot connect to Gramps API: {e}") from e
        except httpx.TimeoutException as e:
            raise GrampsAPIError(f"Request timeout: {e}") from e
        except Exception as e:
            raise GrampsAPIError(f"Unexpected error: {e}") from e

    def _format_http_error(self, error: httpx.HTTPStatusError) -> str:
        """Convert HTTP error to user-friendly message."""
        status_code = error.response.status_code

        if status_code == 401:
            return "Authentication failed. Please check your credentials."
        elif status_code == 403:
            return "Permission denied for this operation."
        elif status_code == 404:
            return "Record not found."
        elif status_code == 422:
            return "Invalid data provided."
        elif status_code >= 500:
            return "Server error. Please try again later."
        else:
            return f"Request failed with status {status_code}"

    def _build_url_with_substitution(
        self, tree_id: str, endpoint: str, url_params: Dict
    ) -> str:
        """
        Build URL with parameter substitution for dynamic endpoints.

        Args:
            tree_id: Family tree identifier
            endpoint: API endpoint with potential placeholders (e.g., "people/{handle}")
            url_params: Parameters to substitute in the endpoint

        Returns:
            Complete URL with parameters substituted
        """
        # Substitute URL parameters in the endpoint
        substituted_endpoint = endpoint
        for param_name, param_value in url_params.items():
            placeholder = f"{{{param_name}}}"
            if placeholder in substituted_endpoint:
                substituted_endpoint = substituted_endpoint.replace(
                    placeholder, str(param_value)
                )

        # Check if all required parameters were provided
        remaining_placeholders = re.findall(r"\{([^}]+)\}", substituted_endpoint)
        if remaining_placeholders:
            raise ValueError(
                f"Missing required URL parameters: {remaining_placeholders}"
            )

        return self._build_url(tree_id, substituted_endpoint)

    async def make_api_call(
        self,
        api_call: ApiCalls,
        params: Optional[Union[Dict, BaseModel]] = None,
        tree_id: str = "default",
        with_headers: bool = False,
        **url_params,
    ):
        """
        Make a unified API call using the ApiCalls enum.

        Args:
            api_call: The API call to make from the ApiCalls enum
            params: Parameters for the API call (dict or Pydantic model)
            tree_id: Family tree identifier (default: "default")
            **url_params: URL parameters for endpoint substitution
                (e.g., handle, handle1, handle2)

        Returns:
            API response data

        Raises:
            GrampsAPIError: If the API call fails
            ValueError: If parameters are invalid for the given API call
        """
        # Validate parameters using the mapped parameter model
        validated_params = None
        if params is not None:
            if isinstance(params, BaseModel):
                validated_params = params
            else:
                validated_params = validate_api_call_params(api_call, params)

        # Build the URL with parameter substitution
        endpoint = api_call.endpoint

        # Add tree_id to url_params if endpoint needs it
        if "{tree_id}" in endpoint:
            url_params = dict(url_params)  # Make a copy
            url_params["tree_id"] = tree_id

        url = self._build_url_with_substitution(tree_id, endpoint, url_params)

        # Prepare request parameters
        request_params = None
        json_data = None

        if validated_params is not None:
            params_dict = validated_params.model_dump(exclude_none=True)
            # POST and PUT operations use JSON body, GET operations use query parameters
            if (
                api_call.method in ["POST", "PUT"]
                and api_call != ApiCalls.POST_REPORT_FILE
            ):
                json_data = params_dict
            else:
                request_params = params_dict

        # For PUT operations, preserve existing data by merging with changes
        if api_call.method == "PUT" and json_data:
            handle = url_params.get("handle") or json_data.get("handle")
            if handle:
                # Use same endpoint for GET (remove method-specific parts if any)
                get_endpoint = endpoint
                get_url = self._build_url_with_substitution(
                    tree_id, get_endpoint, {"handle": handle}
                )
                existing = await self._make_request("GET", get_url)
                if existing:
                    # Merge existing data with changes
                    merged_data = existing.copy()

                    # Merge all fields properly - lists get concatenated,
                    # others get replaced
                    for key, value in json_data.items():
                        if (
                            key.endswith("_list")
                            and isinstance(value, list)
                            and key in existing
                        ):
                            existing_items = existing.get(key, [])

                            # Smart deduplication based on list content type
                            if existing_items and value:
                                # Check if items are objects with 'ref' field
                                # (like event_ref_list, media_list)
                                sample_existing = (
                                    existing_items[0] if existing_items else None
                                )
                                sample_new = value[0] if value else None

                                if (
                                    isinstance(sample_existing, dict)
                                    and "ref" in sample_existing
                                    and isinstance(sample_new, dict)
                                    and "ref" in sample_new
                                ):
                                    # Deduplicate reference objects based on 'ref' field
                                    existing_refs = {
                                        item.get("ref")
                                        for item in existing_items
                                        if isinstance(item, dict)
                                    }
                                    new_items = [
                                        item
                                        for item in value
                                        if isinstance(item, dict)
                                        and item.get("ref") not in existing_refs
                                    ]
                                    merged_data[key] = existing_items + new_items
                                elif isinstance(sample_existing, str) and isinstance(
                                    sample_new, str
                                ):
                                    # Deduplicate simple string handles
                                    existing_set = set(existing_items)
                                    new_items = [
                                        item
                                        for item in value
                                        if item not in existing_set
                                    ]
                                    merged_data[key] = existing_items + new_items
                                else:
                                    # Fallback: simple concatenation for
                                    # mixed/unknown types
                                    merged_data[key] = existing_items + value
                            else:
                                # If either list is empty, just concatenate
                                merged_data[key] = existing_items + value
                        else:
                            merged_data[key] = value
                    json_data = merged_data

        # Make the API request
        return await self._make_request(
            method=api_call.method,
            url=url,
            params=request_params,
            json_data=json_data,
            return_headers=with_headers,
        )

    async def upload_media_file(
        self, file_content: bytes, mime_type: str, tree_id: str = "default"
    ):
        """Upload a media file to Gramps."""
        url = self._build_url(tree_id, "media/")
        headers = await self._get_headers()
        headers["Content-Type"] = mime_type

        response = await self.auth_manager.client.request(
            method="POST", url=url, content=file_content, headers=headers
        )
        response.raise_for_status()
        return response.json()


# Export the main classes for easy import
__all__ = [
    "GrampsWebAPIClient", "GrampsAPIError",
    "get_client", "open_database", "close_database", "list_databases",
]


_direct_client_singleton = None
_direct_client_path: str = ""


def _is_sqlite_path(path: str) -> bool:
    """Return True if *path* points to a Gramps SQLite database."""
    import os
    if path.lower().endswith((".sqlite", ".db")):
        return True
    if os.path.isdir(path) and os.path.exists(os.path.join(path, "sqlite.db")):
        return True
    return False


def get_client():
    """
    Return the active Gramps client.

    Priority order:

    1. **Runtime singleton** — set by :func:`open_database` (the
       ``open_database`` MCP tool).  This takes precedence over all env
       vars so the agent can switch databases at runtime without
       restarting the server.

    2. **``GRAMPS_DB_PATH`` env var** — path to a ``.sqlite`` /
       ``.gpkg`` / ``.gramps`` file.  A new client is created and cached
       as a singleton.

    3. **``GRAMPS_API_URL`` env var** — fall back to
       :class:`GrampsWebAPIClient`.

    4. **Nothing configured** — raises :class:`GrampsAPIError` with a
       hint to call ``list_databases`` / ``open_database``.

    Returns:
        The active client instance.

    Raises:
        GrampsAPIError: If no database is currently open or configured.
    """
    global _direct_client_singleton, _direct_client_path

    # 1. Runtime singleton (set by open_database tool)
    if _direct_client_singleton is not None:
        return _direct_client_singleton

    # 2. GRAMPS_DB_PATH env var
    settings = get_settings()
    if settings.use_direct_backend:
        path = settings.gramps_db_path
        if _is_sqlite_path(path):
            from .sqlite_client import GrampsSqliteClient
            locked_by = _read_lock(path)
            externally_locked = bool(
                locked_by and "gramps_mcp" not in locked_by
            )
            if externally_locked:
                logger.warning(
                    "Database '%s' locked by '%s' — opening read-only.",
                    path, locked_by,
                )
            _direct_client_singleton = GrampsSqliteClient(
                path, read_only=externally_locked
            )
            if not externally_locked:
                _write_lock(path)
        else:
            from .direct_client import GrampsDirectClient
            _direct_client_singleton = GrampsDirectClient(path)
        _direct_client_path = path
        return _direct_client_singleton

    # 3. GRAMPS_API_URL env var
    if settings.gramps_api_url:
        return GrampsWebAPIClient()

    # 4. Nothing configured
    raise GrampsAPIError(
        "No database connected. "
        "Use list_databases to see available Gramps trees, "
        "then open_database(path) to connect."
    )


def _lock_dir(db_path: str) -> str:
    """Return the tree directory that contains the Gramps lock file."""
    import os
    if os.path.isfile(db_path):
        return os.path.dirname(db_path)
    return db_path


def _lock_path(db_path: str) -> str:
    """Return the path to the Gramps lock file for a database."""
    import os
    return os.path.join(_lock_dir(db_path), "lock")


def _read_lock(db_path: str) -> str:
    """Return the content of the lock file, or '' if no lock exists."""
    import os
    p = _lock_path(db_path)
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            pass
    return ""


def _write_lock(db_path: str) -> None:
    """Write a Gramps-compatible lock file so Desktop sees the agent."""
    import socket
    content = f"gramps_mcp@{socket.gethostname()}"
    try:
        with open(_lock_path(db_path), "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as exc:
        logger.warning(
            "Could not write Gramps lock file '%s': %s — "
            "Gramps Desktop may not see this agent as active.",
            _lock_path(db_path), exc,
        )


def _clear_lock(db_path: str) -> None:
    """Remove the lock file written by this process."""
    import os
    p = _lock_path(db_path)
    try:
        if os.path.exists(p):
            content = _read_lock(db_path)
            if "gramps_mcp" in content:
                os.remove(p)
    except OSError:
        pass


def _gramps_db_root() -> str:
    """
    Return the platform-specific Gramps grampsdb directory.

    Returns:
        Absolute path to the grampsdb directory, or empty string if not found.
    """
    import os
    import sys
    candidates = []
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            candidates.append(os.path.join(appdata, "gramps", "grampsdb"))
    else:
        home = os.path.expanduser("~")
        candidates += [
            os.path.join(home, ".local", "share", "gramps", "grampsdb"),
            os.path.join(home, ".gramps", "grampsdb"),
        ]
    for path in candidates:
        if os.path.isdir(path):
            return path
    return ""


def list_databases() -> list:
    """
    Return metadata for every Gramps database found on this machine.

    Reads the Gramps ``grampsdb`` directory and inspects each tree's
    ``name.txt`` and ``database.txt`` files.

    Returns:
        List of dicts with keys: ``id``, ``name``, ``backend``,
        ``path`` (to the SQLite file or directory), ``writable``.
    """
    import os
    root = _gramps_db_root()
    if not root:
        return []
    results = []
    for entry in sorted(os.listdir(root)):
        tree_dir = os.path.join(root, entry)
        if not os.path.isdir(tree_dir):
            continue
        name_file = os.path.join(tree_dir, "name.txt")
        backend_file = os.path.join(tree_dir, "database.txt")
        name = ""
        backend = ""
        if os.path.exists(name_file):
            with open(name_file, encoding="utf-8") as f:
                name = f.read().strip()
        if os.path.exists(backend_file):
            with open(backend_file, encoding="utf-8") as f:
                backend = f.read().strip()
        sqlite_path = os.path.join(tree_dir, "sqlite.db")
        if os.path.exists(sqlite_path):
            db_path = sqlite_path
            writable = True
        else:
            db_path = tree_dir
            writable = False
        locked_by = _read_lock(tree_dir)
        results.append({
            "id": entry,
            "name": name or entry,
            "backend": backend or "unknown",
            "path": db_path,
            "writable": writable,
            "locked_by": locked_by,
        })
    return results


def _close_singleton() -> None:
    """Close the current singleton's DB connection if it has one."""
    global _direct_client_singleton
    if _direct_client_singleton is None:
        return
    db = getattr(_direct_client_singleton, "_db", None)
    if db is not None and hasattr(db, "close"):
        try:
            db.close()
        except Exception:
            pass
    _direct_client_singleton = None


def open_database(path: str):
    """
    Open a Gramps database, replacing any currently active singleton.

    Accepts ``.sqlite`` / ``.db`` files (or directories containing
    ``sqlite.db``) for full read/write access, or ``.gpkg`` / ``.gramps``
    files for read-only access.

    Checks for an existing Gramps lock file and logs a warning if Gramps
    Desktop appears to have the database open.  Writes its own lock file
    (``lock`` containing ``gramps_mcp@<hostname>``) so Gramps Desktop will
    show a "database in use" dialog if the user tries to open it.

    Args:
        path: Absolute path to the database file or directory.

    Returns:
        Tuple ``(client, locked_by)`` where *locked_by* is a non-empty
        string if a pre-existing lock was found, else empty string.

    Raises:
        GrampsAPIError: If the path does not exist or is not recognised.
    """
    global _direct_client_singleton, _direct_client_path
    import os
    if not os.path.exists(path):
        raise GrampsAPIError(f"Database path not found: '{path}'")
    _close_singleton()

    locked_by = _read_lock(path)
    externally_locked = bool(locked_by and "gramps_mcp" not in locked_by)

    if _is_sqlite_path(path):
        from .sqlite_client import GrampsSqliteClient
        if externally_locked:
            logger.warning(
                "Database '%s' locked by '%s' — opening read-only.",
                path, locked_by,
            )
        _direct_client_singleton = GrampsSqliteClient(
            path, read_only=externally_locked
        )
        if not externally_locked:
            _write_lock(path)
    else:
        from .direct_client import GrampsDirectClient
        _direct_client_singleton = GrampsDirectClient(path)

    _direct_client_path = path
    return _direct_client_singleton, locked_by


def close_database() -> str:
    """
    Close the current database connection and release the singleton.

    For SQLite databases, also removes the Gramps lock file written by
    :func:`open_database` so Gramps Desktop can open cleanly.
    For XML/gpkg files, the lock step is skipped (no lock is written for
    read-only backends).

    Returns:
        Path of the database that was closed, or empty string if none
        was open.
    """
    global _direct_client_path
    path = _direct_client_path
    if path and _is_sqlite_path(path):
        _clear_lock(path)
    _close_singleton()
    _direct_client_path = ""  # reset so close is idempotent and path is not stale
    return path


