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
GrampsSqliteClient — full read/write client for local Gramps SQLite databases.

Drop-in replacement for GrampsWebAPIClient that connects directly to the
Gramps SQLite file (grampsdb/<id>/sqlite.db).  No GTK, no Gramps Python
package, no web server required.

Supports all read AND write operations.  Changes are written transactionally
to SQLite and immediately visible in the in-memory cache used for subsequent
reads.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from ._gql import gql_match
from ._gramps_sqlite import GrampsSqliteDB, _load_sqlite
from .client import GrampsAPIError
from .models.api_calls import ApiCalls

logger = logging.getLogger(__name__)

# Object types handled by generic GET/LIST/POST/PUT
_OBJ_TYPES = {
    ApiCalls.GET_PERSON: ("person", True),
    ApiCalls.GET_PEOPLE: ("person", False),
    ApiCalls.GET_FAMILY: ("family", True),
    ApiCalls.GET_FAMILIES: ("family", False),
    ApiCalls.GET_EVENT: ("event", True),
    ApiCalls.GET_EVENTS: ("event", False),
    ApiCalls.GET_PLACE: ("place", True),
    ApiCalls.GET_PLACES: ("place", False),
    ApiCalls.GET_SOURCE: ("source", True),
    ApiCalls.GET_SOURCES: ("source", False),
    ApiCalls.GET_CITATION: ("citation", True),
    ApiCalls.GET_CITATIONS: ("citation", False),
    ApiCalls.GET_NOTE: ("note", True),
    ApiCalls.GET_NOTES: ("note", False),
    ApiCalls.GET_MEDIA_ITEM: ("media", True),
    ApiCalls.GET_MEDIA: ("media", False),
    ApiCalls.GET_REPOSITORY: ("repository", True),
    ApiCalls.GET_REPOSITORIES: ("repository", False),
}
_WRITE_MAP = {
    ApiCalls.POST_PEOPLE: "person", ApiCalls.PUT_PERSON: "person",
    ApiCalls.POST_FAMILIES: "family", ApiCalls.PUT_FAMILY: "family",
    ApiCalls.POST_EVENTS: "event", ApiCalls.PUT_EVENT: "event",
    ApiCalls.POST_PLACES: "place", ApiCalls.PUT_PLACE: "place",
    ApiCalls.POST_SOURCES: "source", ApiCalls.PUT_SOURCE: "source",
    ApiCalls.POST_CITATIONS: "citation", ApiCalls.PUT_CITATION: "citation",
    ApiCalls.POST_NOTES: "note", ApiCalls.PUT_NOTE: "note",
    ApiCalls.POST_MEDIA: "media", ApiCalls.PUT_MEDIA_ITEM: "media",
    ApiCalls.POST_REPOSITORIES: "repository", ApiCalls.PUT_REPOSITORY: "repository",
}


class GrampsSqliteClient:
    """
    Full read/write MCP client backed by a Gramps SQLite database.

    All MCP tools work unchanged — the same ``make_api_call()`` interface
    as GrampsWebAPIClient and GrampsDirectClient.
    """

    def __init__(self, db_path: str, read_only: bool = False):
        """
        Open the Gramps SQLite database and load all objects into memory.

        Args:
            db_path:   Absolute path to the Gramps ``sqlite.db`` file, or to
                the grampsdb tree directory (which contains ``sqlite.db``).
            read_only: If True, write operations raise :class:`GrampsAPIError`.
                Set automatically when another process holds the lock file.
        """
        if os.path.isdir(db_path):
            db_path = os.path.join(db_path, "sqlite.db")
        self._db: GrampsSqliteDB = _load_sqlite(db_path, read_only=read_only)
        self._db_path = db_path
        self._report_cache: Dict[str, str] = {}

    async def close(self):
        """
        No-op: the connection is managed by the singleton lifecycle.

        Actual cleanup happens via _close_singleton() → _db.close() when
        close_database() is called explicitly.  Calling this method from the
        with_client decorator after every tool call must not destroy the
        connection that the singleton still holds.
        """

    # ------------------------------------------------------------------
    # Public interface  (identical to GrampsWebAPIClient / GrampsDirectClient)
    # ------------------------------------------------------------------

    async def make_api_call(
        self,
        api_call: ApiCalls,
        params: Optional[Union[Dict, BaseModel]] = None,
        tree_id: str = "default",
        with_headers: bool = False,
        **url_params,
    ):
        """
        Dispatch an API call to the in-memory Gramps SQLite database.

        Args:
            api_call:     The API endpoint to call (from ApiCalls enum).
            params:       Query parameters as a dict or Pydantic model.
            tree_id:      Ignored; present for interface compatibility.
            with_headers: If True, return ``(result, headers)`` tuple.
            **url_params: Path parameters such as ``handle``.

        Returns:
            The API result (list or dict), or a (result, headers) tuple
            when *with_headers* is True.

        Raises:
            GrampsAPIError: On missing required parameters or DB errors.
        """
        params_dict: Dict = {}
        if params is not None:
            if isinstance(params, BaseModel):
                params_dict = params.model_dump(exclude_none=True)
            elif isinstance(params, dict):
                params_dict = params

        result = self._dispatch(api_call, params_dict, url_params)

        if with_headers:
            count = len(result) if isinstance(result, list) else 1
            return result, {"x-total-count": str(count)}
        return result

    async def upload_media_file(
        self, file_content: bytes, mime_type: str, tree_id: str = "default"
    ):
        """
        Not yet implemented for the SQLite backend.

        Args:
            file_content: Raw file bytes (unused).
            mime_type:    MIME type (unused).
            tree_id:      Tree identifier (unused).

        Raises:
            GrampsAPIError: Always — file upload is not yet supported.
        """
        raise GrampsAPIError(
            "upload_media_file is not yet supported in the SQLite backend."
        )

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, api_call: ApiCalls, params: Dict, url_params: Dict) -> Any:
        handle = url_params.get("handle")
        extend = params.get("extend") == "all"

        # Generic GET single / GET list
        if api_call in _OBJ_TYPES:
            obj_type, is_single = _OBJ_TYPES[api_call]
            if is_single:
                return self._get_single(obj_type, handle, extend)
            return self._get_list(obj_type, params)

        # Write operations
        if api_call in _WRITE_MAP:
            obj_type = _WRITE_MAP[api_call]
            is_put = api_call.name.startswith("PUT_")
            # Strip MCP query params that must not be persisted as object fields.
            _meta = {"extend", "pagesize", "page", "gramps_id", "gql",
                     "query", "name", "search"}
            body = {k: v for k, v in params.items() if k not in _meta}
            if is_put and handle:
                body = {**body, "handle": handle}
            return self._db.put(obj_type, body)

        # Search
        if api_call == ApiCalls.GET_SEARCH:
            return self._search(params)

        # Tree info
        if api_call == ApiCalls.GET_TREE:
            return self._get_tree_info()

        # Timelines
        if api_call == ApiCalls.GET_PERSON_TIMELINE:
            return self._db.build_person_timeline(handle)
        if api_call == ApiCalls.GET_FAMILY_TIMELINE:
            return self._db.build_family_timeline(handle)

        # Reports (BFS ancestor / descendant)
        if api_call == ApiCalls.POST_REPORT_FILE:
            report_id = url_params.get("report_id", "")
            if report_id in ("ancestor_report", "descend_report"):
                return self._generate_report(report_id, params)
            raise GrampsAPIError(
                f"POST_REPORT_FILE for '{report_id}' is not supported in SQLite mode."
            )
        if api_call == ApiCalls.GET_REPORT_PROCESSED:
            filename = url_params.get("filename", "")
            if filename in self._report_cache:
                return {"raw_content": self._report_cache[filename]}
            raise GrampsAPIError(
                f"No cached report for '{filename}'. Call POST_REPORT_FILE first."
            )

        if api_call in (
            ApiCalls.GET_REPORT_FILE,
            ApiCalls.GET_TASK_STATUS,
            ApiCalls.GET_TRANSACTIONS_HISTORY,
            ApiCalls.GET_TRANSACTION_HISTORY,
        ):
            raise GrampsAPIError(
                f"{api_call.name} is not supported in the SQLite backend."
            )

        raise GrampsAPIError(
            f"API call {api_call.name} is not implemented in the SQLite backend."
        )

    # ------------------------------------------------------------------
    # GET single
    # ------------------------------------------------------------------

    def _get_single(self, obj_type: str, handle: str, extend: bool) -> Dict:
        """
        Retrieve one object by handle.

        Args:
            obj_type: Object type string.
            handle:   Gramps handle.
            extend:   If True, attach related objects in ``extended`` block.

        Returns:
            The object dict.

        Raises:
            GrampsAPIError: If handle is empty or object not found.
        """
        if not handle:
            raise GrampsAPIError(f"handle is required for GET {obj_type}")
        obj = self._db.get(obj_type, handle)
        if obj is None:
            raise GrampsAPIError(f"{obj_type} with handle '{handle}' not found")
        if extend:
            if obj_type == "person":
                obj = {**obj, "extended": self._db.build_extended_person(obj)}
            elif obj_type == "family":
                obj = {**obj, "extended": self._db.build_extended_family(obj)}
        return obj

    # ------------------------------------------------------------------
    # GET list
    # ------------------------------------------------------------------

    def _get_list(self, obj_type: str, params: Dict) -> List[Dict]:
        """
        List objects with optional filtering and pagination.

        Args:
            obj_type: Object type string.
            params:   Query parameters (pagesize, page, gramps_id, gql, …).

        Returns:
            Paginated list of matching object dicts.
        """
        pagesize = int(params.get("pagesize", 20))
        page = int(params.get("page", 1))
        name_filter = (
            params.get("name") or params.get("search") or params.get("query") or ""
        ).lower()
        gramps_id_filter = params.get("gramps_id", "")
        gql = params.get("gql", "")

        # Fast path: gramps_id is SQL-indexed — skip the full table scan.
        if gramps_id_filter and not name_filter and not gql:
            obj = self._db.get_by_id(obj_type, gramps_id_filter)
            return [obj] if obj else []

        results = []
        for obj in self._db.all(obj_type):
            if gramps_id_filter and obj.get("gramps_id") != gramps_id_filter:
                continue
            if name_filter and not self._text_match(obj_type, obj, name_filter):
                continue
            if gql and not gql_match(obj, gql):
                continue
            results.append(obj)

        start = (page - 1) * pagesize
        return results[start: start + pagesize]

    def _text_match(self, obj_type: str, obj: Dict, query: str) -> bool:
        """Substring match for list filtering (same logic as GrampsDirectClient)."""
        if obj_type == "person":
            pn = obj.get("primary_name", {})
            first = pn.get("first_name", "").lower()
            surnames = " ".join(
                s.get("surname", "") for s in pn.get("surname_list", [])
            ).lower()
            return query in first or query in surnames
        if obj_type in ("source", "repository"):
            return query in obj.get("title", obj.get("name", "")).lower()
        if obj_type == "place":
            return query in obj.get("title", "").lower() or query in obj.get(
                "name", {}
            ).get("value", "").lower()
        if obj_type == "note":
            text = obj.get("text", {})
            s = text.get("string", "") if isinstance(text, dict) else str(text)
            return query in s.lower()
        if obj_type == "event":
            return query in obj.get("type", "").lower() or query in obj.get(
                "description", ""
            ).lower()
        return query in obj.get("gramps_id", "").lower()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _search(self, params: Dict) -> List[Dict]:
        """Full-text search across all object types."""
        query = (params.get("query") or "").lower()
        pagesize = int(params.get("pagesize", 20))
        if not query:
            return []
        results = []
        for obj_type in (
            "person", "family", "event", "place",
            "source", "citation", "note", "media", "repository",
        ):
            if len(results) >= pagesize:
                break
            for obj in self._db.all(obj_type):
                if len(results) >= pagesize:
                    break
                if self._text_match(obj_type, obj, query):
                    results.append({"object_type": obj_type, "object": obj})
        return results

    # ------------------------------------------------------------------
    # Tree info
    # ------------------------------------------------------------------

    def _get_tree_info(self) -> Dict:
        """Return tree statistics."""
        return {
            "id": "sqlite",
            "name": os.path.basename(os.path.dirname(self._db_path)),
            "description": f"Direct SQLite access: {os.path.basename(self._db_path)}",
            "usage_people": self._db.count("person"),
            "usage_families": self._db.count("family"),
            "usage_events": self._db.count("event"),
            "usage_places": self._db.count("place"),
            "usage_sources": self._db.count("source"),
            "usage_citations": self._db.count("citation"),
            "usage_media": self._db.count("media"),
            "usage_notes": self._db.count("note"),
            "usage_repositories": self._db.count("repository"),
        }

    # ------------------------------------------------------------------
    # Reports  (BFS traversal — same as GrampsDirectClient)
    # ------------------------------------------------------------------

    def _generate_report(self, report_id: str, params: Dict) -> Dict:
        """Run an ancestor or descendant report and cache the HTML result."""

        options_raw = params.get("options", "{}")
        try:
            options = json.loads(options_raw) if options_raw else {}
        except (json.JSONDecodeError, TypeError):
            options = {}

        pid = options.get("pid", "")
        person = self._db.get_by_id("person", pid) if pid else None
        if not person:
            raise GrampsAPIError(f"Person with Gramps ID '{pid}' not found.")

        if report_id == "ancestor_report":
            max_gen = int(options.get("maxgen", 5))
            html = self._traverse_ancestors(person, max_gen)
        else:
            max_gen = int(options.get("gen", 5))
            html = self._traverse_descendants(person, max_gen)

        cache_key = f"sqlite_{report_id}_{pid}"
        self._report_cache[cache_key] = html
        return {"file_name": cache_key}

    def _traverse_ancestors(self, start: Dict, max_gen: int) -> str:
        """Delegate to GrampsXmlDB.traverse_ancestors (single implementation)."""
        return self._db.traverse_ancestors(start, max_gen)

    def _traverse_descendants(self, start: Dict, max_gen: int) -> str:
        """Delegate to GrampsXmlDB.traverse_descendants (single implementation)."""
        return self._db.traverse_descendants(start, max_gen)
