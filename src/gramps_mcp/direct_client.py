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
Direct Gramps XML client.

Reads .gpkg files (or .gramps XML files) without requiring the Gramps Python
package or any GTK/GLib system libraries. Uses Python's built-in xml.etree
and tarfile/gzip modules only.

Read-only. Write operations raise GrampsAPIError with a clear message.
Ancestors and descendants are resolved via in-memory BFS traversal.

Supported GRAMPS_DB_PATH values:
  - Absolute path to a .gpkg file (tar.gz with .gramps XML inside)
  - Absolute path to a plain .gramps XML file (gzip-compressed or plain)
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from ._gql import gql_match
from ._gramps_db import _load_gpkg
from .client import GrampsAPIError
from .models.api_calls import ApiCalls

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# GrampsDirectClient
# ---------------------------------------------------------------------------


class GrampsDirectClient:
    """
    Drop-in replacement for GrampsWebAPIClient that reads a local .gpkg file
    directly — no Gramps Python package, no GTK/GLib, no web server required.

    The only public method is make_api_call(), which mirrors GrampsWebAPIClient.
    Write operations (POST/PUT) raise GrampsAPIError; read-only for now.
    Ancestors/descendants are handled via in-memory BFS traversal.
    """

    def __init__(self, db_path: str):
        self._db = _load_gpkg(db_path)
        self._db_path = db_path
        self._report_cache: Dict[str, str] = {}

    async def close(self):
        pass  # Nothing to close for an in-memory store

    # ------------------------------------------------------------------
    # Public interface
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
        Dispatch an API call to the in-memory Gramps database.

        Mirrors the GrampsWebAPIClient interface so all MCP tools work
        without modification.  Write operations raise GrampsAPIError.

        Args:
            api_call: The API endpoint to call (from ApiCalls enum).
            params: Query parameters as a dict or Pydantic model.
            tree_id: Ignored; present for interface compatibility.
            with_headers: If True, return (result, headers) tuple where
                headers contains ``x-total-count``.
            **url_params: Path parameters such as ``handle``, ``report_id``,
                or ``filename``.

        Returns:
            The API result (list or dict), or a (result, headers) tuple
            when *with_headers* is True.

        Raises:
            GrampsAPIError: For write operations or unsupported calls.
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
        Not supported in direct (read-only) mode.

        Args:
            file_content: Raw file bytes (unused).
            mime_type: MIME type of the file (unused).
            tree_id: Tree identifier (unused).

        Raises:
            GrampsAPIError: Always — the direct backend is read-only.
        """
        raise GrampsAPIError(
            "upload_media_file is not supported in direct (read-only) mode."
        )

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, api_call: ApiCalls, params: Dict, url_params: Dict) -> Any:
        handle = url_params.get("handle")
        extend = params.get("extend") == "all"

        # People
        if api_call == ApiCalls.GET_PERSON:
            return self._get_single("person", handle, extend)
        if api_call == ApiCalls.GET_PEOPLE:
            return self._get_list("person", params)

        # Families
        if api_call == ApiCalls.GET_FAMILY:
            return self._get_single("family", handle, extend)
        if api_call == ApiCalls.GET_FAMILIES:
            return self._get_list("family", params)

        # Events
        if api_call == ApiCalls.GET_EVENT:
            return self._get_single("event", handle, False)
        if api_call == ApiCalls.GET_EVENTS:
            return self._get_list("event", params)

        # Places
        if api_call == ApiCalls.GET_PLACE:
            return self._get_single("place", handle, False)
        if api_call == ApiCalls.GET_PLACES:
            return self._get_list("place", params)

        # Sources
        if api_call == ApiCalls.GET_SOURCE:
            return self._get_single("source", handle, False)
        if api_call == ApiCalls.GET_SOURCES:
            return self._get_list("source", params)

        # Citations
        if api_call == ApiCalls.GET_CITATION:
            return self._get_single("citation", handle, False)
        if api_call == ApiCalls.GET_CITATIONS:
            return self._get_list("citation", params)

        # Notes
        if api_call == ApiCalls.GET_NOTE:
            return self._get_single("note", handle, False)
        if api_call == ApiCalls.GET_NOTES:
            return self._get_list("note", params)

        # Media
        if api_call == ApiCalls.GET_MEDIA_ITEM:
            return self._get_single("media", handle, False)
        if api_call == ApiCalls.GET_MEDIA:
            return self._get_list("media", params)

        # Repositories
        if api_call == ApiCalls.GET_REPOSITORY:
            return self._get_single("repository", handle, False)
        if api_call == ApiCalls.GET_REPOSITORIES:
            return self._get_list("repository", params)

        # Search
        if api_call == ApiCalls.GET_SEARCH:
            return self._search(params)

        # Tree info
        if api_call == ApiCalls.GET_TREE:
            return self._get_tree_info()

        # Ancestor / descendant reports (intercepted before the write-op block)
        if api_call == ApiCalls.POST_REPORT_FILE:
            report_id = url_params.get("report_id", "")
            if report_id in ("ancestor_report", "descend_report"):
                return self._generate_report(report_id, params)
            raise GrampsAPIError(
                f"POST_REPORT_FILE for report '{report_id}' is not supported "
                "in direct mode. Only ancestor_report and descend_report are available."
            )

        if api_call == ApiCalls.GET_REPORT_PROCESSED:
            filename = url_params.get("filename", "")
            if filename in self._report_cache:
                return {"raw_content": self._report_cache[filename]}
            raise GrampsAPIError(
                f"No cached report for '{filename}'. "
                "Call POST_REPORT_FILE first to generate the report."
            )

        # Timelines
        if api_call == ApiCalls.GET_PERSON_TIMELINE:
            return self._db.build_person_timeline(handle)
        if api_call == ApiCalls.GET_FAMILY_TIMELINE:
            return self._db.build_family_timeline(handle)

        # Write operations — not supported in read-only direct mode
        if api_call in (
            ApiCalls.POST_PEOPLE, ApiCalls.PUT_PERSON,
            ApiCalls.POST_FAMILIES, ApiCalls.PUT_FAMILY,
            ApiCalls.POST_EVENTS, ApiCalls.PUT_EVENT,
            ApiCalls.POST_PLACES, ApiCalls.PUT_PLACE,
            ApiCalls.POST_SOURCES, ApiCalls.PUT_SOURCE,
            ApiCalls.POST_CITATIONS, ApiCalls.PUT_CITATION,
            ApiCalls.POST_NOTES, ApiCalls.PUT_NOTE,
            ApiCalls.POST_MEDIA, ApiCalls.PUT_MEDIA_ITEM,
            ApiCalls.POST_REPOSITORIES, ApiCalls.PUT_REPOSITORY,
        ):
            raise GrampsAPIError(
                f"{api_call.name} requires write access. "
                "The direct backend currently supports read-only operations. "
                "To create or update records, use a Gramps Web API server."
            )

        # Unsupported
        if api_call in (
            ApiCalls.GET_REPORT_FILE,
            ApiCalls.GET_TASK_STATUS,
            ApiCalls.GET_TRANSACTIONS_HISTORY,
            ApiCalls.GET_TRANSACTION_HISTORY,
        ):
            raise GrampsAPIError(
                f"{api_call.name} is not supported in direct mode. "
                "These operations require a running Gramps Web API server."
            )

        raise GrampsAPIError(
            f"API call {api_call.name} is not implemented in the direct backend."
        )

    # ------------------------------------------------------------------
    # GET single
    # ------------------------------------------------------------------

    def _get_single(self, obj_type: str, handle: str, extend: bool) -> Dict:
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
        pagesize = int(params.get("pagesize", 20))
        page = int(params.get("page", 1))
        name_filter = (
            params.get("name") or params.get("search") or params.get("query") or ""
        ).lower()
        gramps_id_filter = params.get("gramps_id", "")
        gql = params.get("gql", "")

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
        """Substring match for list filtering."""
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

        return query in obj.get("gramps_id", "").lower() or query in obj.get(
            "description", obj.get("page", obj.get("desc", ""))
        ).lower()

    # ------------------------------------------------------------------
    # Full-text search
    # ------------------------------------------------------------------

    def _search(self, params: Dict) -> List[Dict]:
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
        return {
            "id": "direct",
            "name": os.path.splitext(os.path.basename(self._db_path))[0],
            "description": f"Direct read from {os.path.basename(self._db_path)}",
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
    # Ancestors / descendants (BFS traversal, returns HTML for html_to_markdown)
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
            raise GrampsAPIError(
                f"Person with Gramps ID '{pid}' not found. "
                "Pass pid in the report options."
            )

        if report_id == "ancestor_report":
            max_gen = int(options.get("maxgen", 5))
            html = self._traverse_ancestors(person, max_gen)
        else:
            max_gen = int(options.get("gen", 5))
            html = self._traverse_descendants(person, max_gen)

        cache_key = f"direct_{report_id}_{pid}"
        self._report_cache[cache_key] = html
        return {"file_name": cache_key}

    def _traverse_ancestors(self, start: Dict, max_gen: int) -> str:
        """Delegate to GrampsXmlDB.traverse_ancestors (single implementation)."""
        return self._db.traverse_ancestors(start, max_gen)

    def _traverse_descendants(self, start: Dict, max_gen: int) -> str:
        """Delegate to GrampsXmlDB.traverse_descendants (single implementation)."""
        return self._db.traverse_descendants(start, max_gen)
