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
Gramps SQLite database access layer.

Reads and writes the Gramps SQLite database (grampsdb/*/sqlite.db) directly
using only Python's standard library.  No GTK, no gramps Python package needed.

The Gramps SQLite backend stores each object as JSON in a ``json_data`` column
plus indexed secondary columns.  Typed sub-objects use ``_class`` keys
(e.g. ``{"_class": "EventType", "value": 12, "string": ""}``).

This module normalises that format to the flat-string dict our handlers expect,
and denormalises on write.
"""

import json
import logging
import sqlite3
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from ._gramps_db import GrampsXmlDB
from .client import GrampsAPIError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type maps  (value → display string)
# ---------------------------------------------------------------------------

EVENT_TYPE: Dict[int, str] = {
    -1: "Unknown", 0: "Custom",
    1: "Marriage", 2: "Marriage Settlement", 3: "Marriage License",
    4: "Marriage Contract", 5: "Marriage Banns", 6: "Engagement",
    7: "Divorce", 8: "Divorce Filing", 9: "Annulment",
    10: "Alternate Marriage", 11: "Adopted", 12: "Birth", 13: "Death",
    14: "Adult Christening", 15: "Baptism", 16: "Bar Mitzvah",
    17: "Bat Mitzvah", 18: "Blessing", 19: "Burial", 20: "Cause Of Death",
    21: "Census", 22: "Christening", 23: "Confirmation", 24: "Cremation",
    25: "Degree", 26: "Education", 27: "Elected", 28: "Emigration",
    29: "First Communion", 30: "Immigration", 31: "Graduation",
    32: "Medical Information", 33: "Military Service", 34: "Naturalization",
    35: "Nobility Title", 36: "Number of Marriages", 37: "Occupation",
    38: "Ordination", 39: "Probate", 40: "Property", 41: "Religion",
    42: "Residence", 43: "Retirement", 44: "Will", 45: "Stillbirth",
}
FAMILY_REL_TYPE: Dict[int, str] = {
    0: "Married", 1: "Unmarried", 2: "Civil Union", 3: "Unknown", 4: "Custom",
}
EVENT_ROLE_TYPE: Dict[int, str] = {
    -1: "Unknown", 0: "Custom", 1: "Primary", 2: "Clergy", 3: "Celebrant",
    4: "Aide", 5: "Bride", 6: "Groom", 7: "Witness", 8: "Family",
    9: "Informant", 10: "Godparent", 11: "Father", 12: "Mother",
    13: "Parent", 14: "Child", 15: "Multiple birth", 16: "Friend",
    17: "Neighbor", 18: "Officiator",
}
CHILD_REF_TYPE: Dict[int, str] = {
    0: "None", 1: "Birth", 2: "Adopted", 3: "Stepchild",
    4: "Sponsored", 5: "Foster", 6: "Unknown", 7: "Custom",
}
NAME_TYPE: Dict[int, str] = {
    -1: "Unknown", 0: "Custom", 1: "Also Known As",
    2: "Birth Name", 3: "Married Name",
}
PLACE_TYPE: Dict[int, str] = {
    -1: "Unknown", 0: "Custom", 1: "Country", 2: "State", 3: "County",
    4: "City", 5: "Parish", 6: "Locality", 7: "Street", 8: "Province",
    9: "Region", 10: "Department", 11: "Neighborhood", 12: "District",
    13: "Borough", 14: "Municipality", 15: "Town", 16: "Village",
    17: "Hamlet", 18: "Farm", 19: "Building", 20: "Number",
}

_TYPE_MAPS: Dict[str, Dict[int, str]] = {
    "EventType": EVENT_TYPE,
    "FamilyRelType": FAMILY_REL_TYPE,
    "EventRoleType": EVENT_ROLE_TYPE,
    "ChildRefType": CHILD_REF_TYPE,
    "NameType": NAME_TYPE,
    "PlaceType": PLACE_TYPE,
    "NameOriginType": {},
}
# Custom sentinel value per type class (used when string field is non-empty)
_CUSTOM: Dict[str, int] = {
    "EventType": 0, "FamilyRelType": 4, "EventRoleType": 0,
    "ChildRefType": 7, "NameType": 0, "PlaceType": 0, "NameOriginType": 0,
}
# Reverse maps: display string → int value
_REV_TYPE_MAPS: Dict[str, Dict[str, int]] = {
    cls: {v: k for k, v in m.items()} for cls, m in _TYPE_MAPS.items()
}

# Table name and ID prefix per object type
_TABLE: Dict[str, str] = {
    "person": "person", "family": "family", "event": "event",
    "place": "place", "source": "source", "citation": "citation",
    "note": "note", "media": "media", "repository": "repository",
    "tag": "tag",
}
_ID_PREFIX: Dict[str, str] = {
    "person": "I", "family": "F", "event": "E", "place": "P",
    "source": "S", "citation": "C", "note": "N", "media": "O",
    "repository": "R", "tag": "T",
}

# ---------------------------------------------------------------------------
# Normalisation  (Gramps JSON → our dict format)
# ---------------------------------------------------------------------------


def _type_str(obj: Any) -> str:
    """Convert a typed Gramps JSON object to a plain string."""
    if not isinstance(obj, dict):
        return str(obj) if obj is not None else ""
    cls = obj.get("_class", "")
    string = obj.get("string", "")
    if string:
        return string
    value = obj.get("value", -1)
    return _TYPE_MAPS.get(cls, {}).get(value, f"Unknown({value})")


def _normalize(obj: Any) -> Any:
    """
    Recursively convert Gramps internal JSON to our flat dict format.

    - Typed sub-objects (EventType, etc.) become plain strings.
    - Date objects are reshaped to ``{dateval, modifier, quality, string}``.
    - ``_class`` keys are removed from all other dicts.

    Args:
        obj: Any JSON value from the Gramps sqlite json_data column.

    Returns:
        Normalised value compatible with the Gramps Web API dict shape.
    """
    if isinstance(obj, list):
        return [_normalize(item) for item in obj]
    if not isinstance(obj, dict):
        return obj

    cls = obj.get("_class", "")

    if cls in _TYPE_MAPS:
        return _type_str(obj)

    if cls == "Date":
        return {
            "dateval": obj.get("dateval", []),
            "modifier": obj.get("modifier", 0),
            "quality": obj.get("quality", 0),
            "string": obj.get("text", ""),
        }

    return {k: _normalize(v) for k, v in obj.items() if k != "_class"}


def _normalize_person(raw: Dict) -> Dict:
    """Normalise a raw Gramps person JSON dict."""
    obj = _normalize(raw)
    # birth_ref_index / death_ref_index are already ints in JSON
    return obj


def _normalize_family(raw: Dict) -> Dict:
    """Normalise a raw Gramps family JSON dict (renames type → relationship)."""
    obj = _normalize(raw)
    obj["relationship"] = obj.pop("type", "Married")
    return obj


def _normalize_place(raw: Dict) -> Dict:
    """Normalise a raw Gramps place JSON dict."""
    obj = _normalize(raw)
    # Gramps stores place_type as typed obj; after _normalize it's a string.
    # Re-key to match XML parser output.
    obj["place_type"] = obj.pop("place_type", obj.pop("type", ""))
    return obj


# Generic normaliser for types that need no special treatment
def _normalize_generic(raw: Dict) -> Dict:
    """Normalise a raw Gramps JSON dict."""
    return _normalize(raw)


_NORMALISE: Dict[str, Any] = {
    "person": _normalize_person,
    "family": _normalize_family,
    "place": _normalize_place,
}

# ---------------------------------------------------------------------------
# Denormalisation  (our dict format → Gramps JSON)
# ---------------------------------------------------------------------------


def _denorm_type(value: str, cls: str) -> Dict:
    """
    Convert a plain type string back to a Gramps typed object.

    Args:
        value: Display string, e.g. ``"Birth"``.
        cls:   Gramps class name, e.g. ``"EventType"``.

    Returns:
        Dict like ``{"_class": "EventType", "value": 12, "string": ""}``.
    """
    rev = _REV_TYPE_MAPS.get(cls, {})
    custom = _CUSTOM.get(cls, 0)
    num = rev.get(value, custom)
    return {"_class": cls, "value": num, "string": value if num == custom else ""}


def _denorm_date(d: Any) -> Dict:
    """
    Convert our date dict back to Gramps JSON date format.

    Args:
        d: Our date dict with ``dateval``, ``modifier``, ``quality``, ``string``.

    Returns:
        Gramps JSON date dict with ``_class`` and ``text`` key.
    """
    if not isinstance(d, dict):
        return {"_class": "Date", "calendar": 0, "modifier": 0, "quality": 0,
                "dateval": [], "text": "", "sortval": 0, "newyear": 0, "format": None}
    return {
        "_class": "Date",
        "calendar": d.get("calendar", 0),
        "modifier": d.get("modifier", 0),
        "quality": d.get("quality", 0),
        "dateval": d.get("dateval", []),
        "text": d.get("string", ""),
        "sortval": d.get("sortval", 0),
        "newyear": d.get("newyear", 0),
        "format": d.get("format"),
    }


# ---------------------------------------------------------------------------
# LazyDict — on-demand SQLite proxy replacing the full in-memory dicts
# ---------------------------------------------------------------------------


class LazyDict:
    """
    Dict-like proxy that queries SQLite on every access.

    Implements the subset of the dict interface used by
    :class:`GrampsXmlDB` and its subclasses:
    ``get``, ``__getitem__``, ``__contains__``, ``__len__``,
    ``values``, ``__iter__``, ``__setitem__`` (no-op — data lives in DB).

    Every read goes directly to SQLite so the agent always sees the
    current state of the database without needing a reload.
    """

    def __init__(self, conn: sqlite3.Connection, table: str, normalise):
        """
        Args:
            conn:      Open SQLite connection (row_factory must be sqlite3.Row).
            table:     Table name (e.g. ``"person"``).
            normalise: Callable that converts a raw Gramps JSON dict to our
                       normalised format.
        """
        self._conn = conn
        self._table = table
        self._normalise = normalise

    def _fetch_one(self, handle: str) -> Optional[Dict]:
        """Fetch and normalise a single row by handle, or None."""
        try:
            row = self._conn.execute(  # noqa: S608
                f"SELECT json_data FROM {self._table} WHERE handle=?",
                (handle,),
            ).fetchone()
        except sqlite3.OperationalError:
            return None
        if row is None:
            return None
        try:
            return self._normalise(json.loads(row["json_data"]))
        except Exception:
            return None

    def get(self, handle: Optional[str], default=None):
        """Return the normalised object for *handle*, or *default*."""
        if not handle:
            return default
        result = self._fetch_one(handle)
        return result if result is not None else default

    def __getitem__(self, handle: str) -> Dict:
        result = self._fetch_one(handle)
        if result is None:
            raise KeyError(handle)
        return result

    def __contains__(self, handle: object) -> bool:
        if not isinstance(handle, str):
            return False
        try:
            row = self._conn.execute(  # noqa: S608
                f"SELECT 1 FROM {self._table} WHERE handle=?", (handle,)
            ).fetchone()
            return row is not None
        except sqlite3.OperationalError:
            return False

    def __len__(self) -> int:
        try:
            row = self._conn.execute(  # noqa: S608
                f"SELECT COUNT(*) FROM {self._table}"
            ).fetchone()
            return row[0] if row else 0
        except sqlite3.OperationalError:
            return 0

    def values(self) -> List[Dict]:
        """Return all normalised objects from this table."""
        try:
            rows = self._conn.execute(  # noqa: S608
                f"SELECT json_data FROM {self._table}"
            ).fetchall()
        except sqlite3.OperationalError:
            return []
        result = []
        for row in rows:
            try:
                result.append(self._normalise(json.loads(row["json_data"])))
            except Exception:
                pass
        return result

    def __iter__(self):
        try:
            rows = self._conn.execute(  # noqa: S608
                f"SELECT handle FROM {self._table}"
            ).fetchall()
            return iter(row["handle"] for row in rows)
        except sqlite3.OperationalError:
            return iter([])

    def __setitem__(self, handle: str, value: Dict) -> None:
        """No-op — data is persisted to SQLite by put(), not via dict assignment."""


# ---------------------------------------------------------------------------
# Database loader
# ---------------------------------------------------------------------------


def _load_sqlite(db_path: str, read_only: bool = False) -> "GrampsSqliteDB":
    """
    Open a Gramps SQLite database and return a lazy-loading DB instance.

    No data is loaded eagerly — every read goes directly to SQLite so
    the agent always sees the current state without a reload.

    Args:
        db_path:   Absolute path to the Gramps ``sqlite.db`` file.
        read_only: If True, open in read-only mode (``PRAGMA query_only``).
                   Write attempts will raise :class:`GrampsAPIError`.

    Returns:
        A :class:`GrampsSqliteDB` instance ready for lazy reads and writes.

    Raises:
        GrampsAPIError: If the file cannot be opened or is not a Gramps DB.
    """
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        if read_only:
            conn.execute("PRAGMA query_only=ON")
        else:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
    except Exception as exc:
        raise GrampsAPIError(
            f"Cannot open Gramps SQLite DB '{db_path}': {exc}"
        ) from exc

    logger.info("Opened Gramps SQLite '%s' (read_only=%s)", db_path, read_only)
    return GrampsSqliteDB(conn=conn, db_path=db_path, read_only=read_only)


# ---------------------------------------------------------------------------
# GrampsSqliteDB
# ---------------------------------------------------------------------------


class GrampsSqliteDB(GrampsXmlDB):
    """
    Lazy-loading Gramps database backed by a live SQLite file.

    Inherits all read / traversal / timeline methods from
    :class:`GrampsXmlDB` — they all use ``self.people``,
    ``self.families``, etc. which are now :class:`LazyDict` instances
    that query SQLite on every access.

    This means:
    - No startup delay — nothing is loaded eagerly.
    - Always fresh data — changes made by Gramps Desktop are visible
      immediately on the next read without calling ``reload_database``.
    - Write-through — :meth:`put` writes to SQLite; the next read
      returns the updated data from the DB.
    """

    def __init__(
        self,
        conn: sqlite3.Connection,
        db_path: str,
        read_only: bool = False,
        source_name: str = "",
    ):
        """
        Initialise with an open SQLite connection.

        No data is loaded at construction time — all reads go to SQLite
        on demand via :class:`LazyDict` proxies.

        Args:
            conn:        Open ``sqlite3.Connection`` (row_factory=sqlite3.Row).
            db_path:     Path to the SQLite file (used for logging).
            read_only:   If True, :meth:`put` raises :class:`GrampsAPIError`.
            source_name: Display name shown in log messages.
        """
        # Initialise parent with empty dicts; we replace them immediately.
        super().__init__(
            source_name=source_name or db_path,
            people={}, families={}, events={}, places={},
            sources={}, citations={}, notes={}, media={}, repositories={},
        )
        self._conn = conn
        self._db_path = db_path
        self._read_only = read_only
        self._normalise_map = {
            "person":     _normalize_person,
            "family":     _normalize_family,
            "event":      _normalize_generic,
            "place":      _normalize_place,
            "source":     _normalize_generic,
            "citation":   _normalize_generic,
            "note":       _normalize_generic,
            "media":      _normalize_generic,
            "repository": _normalize_generic,
        }
        # Replace static dicts with live SQLite proxies.
        self.people       = LazyDict(conn, "person",     _normalize_person)
        self.families     = LazyDict(conn, "family",     _normalize_family)
        self.events       = LazyDict(conn, "event",      _normalize_generic)
        self.places       = LazyDict(conn, "place",      _normalize_place)
        self.sources      = LazyDict(conn, "source",     _normalize_generic)
        self.citations    = LazyDict(conn, "citation",   _normalize_generic)
        self.notes        = LazyDict(conn, "note",       _normalize_generic)
        self.media        = LazyDict(conn, "media",      _normalize_generic)
        self.repositories = LazyDict(conn, "repository", _normalize_generic)

    def get_by_id(self, obj_type: str, gramps_id: str) -> Optional[Dict]:
        """
        Look up an object by Gramps ID using the indexed SQL column.

        Faster than the parent's linear scan through ``values()``.

        Args:
            obj_type:  One of ``person``, ``family``, ``event``, etc.
            gramps_id: Gramps ID string, e.g. ``"I0001"``.

        Returns:
            Normalised dict or ``None`` if not found.
        """
        table = _TABLE.get(obj_type)
        normalise = self._normalise_map.get(obj_type)
        if not table or not normalise:
            return None
        try:
            row = self._conn.execute(  # noqa: S608
                f"SELECT json_data FROM {table} WHERE gramps_id=?",
                (gramps_id,),
            ).fetchone()
        except sqlite3.OperationalError:
            return None
        if row is None:
            return None
        try:
            return normalise(json.loads(row["json_data"]))
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Handle / ID generation
    # ------------------------------------------------------------------

    def new_handle(self) -> str:
        """Generate a unique Gramps object handle."""
        return uuid.uuid4().hex

    def _next_id(self, obj_type: str) -> str:
        """
        Return the next available Gramps ID for an object type.

        Args:
            obj_type: One of ``person``, ``family``, ``event``, etc.

        Returns:
            Next ID string, e.g. ``"I0043"``.
        """
        prefix = _ID_PREFIX[obj_type]
        table = _TABLE[obj_type]
        cur = self._conn.execute(
            f"SELECT gramps_id FROM {table} WHERE gramps_id LIKE ?",  # noqa: S608
            (f"{prefix}%",),
        )
        max_num = 0
        for row in cur.fetchall():
            gid = row[0] or ""
            try:
                max_num = max(max_num, int(gid[len(prefix):]))
            except ValueError:
                pass
        return f"{prefix}{max_num + 1:04d}"

    # ------------------------------------------------------------------
    # Write  (INSERT / UPDATE)
    # ------------------------------------------------------------------

    def put(self, obj_type: str, obj: Dict) -> Dict:
        """
        Persist an object to SQLite.

        If ``obj`` has no ``handle``, a new one is generated.
        If ``obj`` has no ``gramps_id``, the next sequential ID is assigned.
        The ``change`` timestamp is always set to now.

        For updates, the existing Gramps JSON is read from the DB, the
        supplied fields are merged in, and the result is written back so
        that fields we do not explicitly touch are preserved.

        Args:
            obj_type: One of ``person``, ``family``, ``event``, etc.
            obj:      Our normalised dict (Gramps Web API shape).

        Returns:
            The stored dict (with handle and gramps_id filled in).

        Raises:
            GrampsAPIError: If the database is read-only or on write errors.
        """
        if self._read_only:
            raise GrampsAPIError(
                "Cannot write: database is open in read-only mode because "
                "another process (Gramps Desktop?) holds the lock file. "
                "Close Gramps Desktop first, then call reload_database."
            )
        handle = obj.get("handle") or self.new_handle()
        obj = {**obj, "handle": handle}

        table = _TABLE[obj_type]
        existing_raw: Optional[Dict] = None

        cur = self._conn.execute(
            f"SELECT json_data FROM {table} WHERE handle = ?",  # noqa: S608
            (handle,),
        )
        row = cur.fetchone()
        if row:
            try:
                existing_raw = json.loads(row[0])
            except Exception:
                pass

        if not obj.get("gramps_id"):
            if existing_raw:
                existing_id = existing_raw.get("gramps_id")
                obj["gramps_id"] = existing_id or self._next_id(obj_type)
            else:
                obj["gramps_id"] = self._next_id(obj_type)

        obj["change"] = int(time.time())

        gramps_json = _build_gramps_json(obj_type, obj, existing_raw)
        json_str = json.dumps(gramps_json, ensure_ascii=False)

        try:
            with self._conn:
                secondaries = _secondaries(obj_type, obj)
                if existing_raw is None:
                    cols = ["handle", "json_data"] + list(secondaries.keys())
                    placeholders = ",".join("?" * len(cols))
                    vals: List = [handle, json_str] + list(secondaries.values())
                    col_str = ",".join(cols)
                    sql = (  # noqa: S608
                        f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})"
                    )
                    self._conn.execute(sql, vals)
                else:
                    update_cols = ["json_data"] + list(secondaries.keys())
                    set_clause = ", ".join(f"{c}=?" for c in update_cols)
                    vals = [json_str] + list(secondaries.values()) + [handle]
                    self._conn.execute(
                        f"UPDATE {table} SET {set_clause} WHERE handle=?",  # noqa: S608
                        vals,
                    )
        except sqlite3.Error as exc:
            raise GrampsAPIError(
                f"SQLite write error for {obj_type}/{handle}: {exc}"
            ) from exc

        # No cache to update — next read fetches fresh from SQLite.
        return obj

    def close(self):
        """Close the SQLite connection."""
        self._conn.close()


# ---------------------------------------------------------------------------
# JSON builder  (our dict → Gramps internal JSON)
# ---------------------------------------------------------------------------


def _build_gramps_json(obj_type: str, obj: Dict, existing: Optional[Dict]) -> Dict:
    """
    Build the Gramps-format JSON dict for storage.

    Merges *obj* into *existing* (if present) so that fields we don't
    touch are preserved.  Typed fields are denormalised back to ``_class``
    objects.

    Args:
        obj_type: One of ``person``, ``family``, ``event``, etc.
        obj:      Our normalised dict.
        existing: Current Gramps JSON from the database (may be None).

    Returns:
        Gramps-format JSON dict ready for ``json.dumps``.
    """
    base = existing.copy() if existing else _empty_gramps_json(obj_type)
    _merge_into(base, obj, obj_type)
    base["handle"] = obj["handle"]
    base["gramps_id"] = obj.get("gramps_id", base.get("gramps_id", ""))
    base["change"] = obj.get("change", int(time.time()))
    base["private"] = bool(obj.get("private", False))
    return base


def _denorm_event_ref(eref: Any) -> Any:
    """Denormalise a single event-ref dict back to Gramps JSON format."""
    if not isinstance(eref, dict):
        return eref
    result = dict(eref)
    result.setdefault("_class", "EventRef")
    if isinstance(result.get("role"), str):
        result["role"] = _denorm_type(result["role"], "EventRoleType")
    result.setdefault("note_list", [])
    result.setdefault("attribute_list", [])
    result.setdefault("private", False)
    return result


def _denorm_child_ref(cref: Any) -> Any:
    """Denormalise a single child-ref dict back to Gramps JSON format."""
    if not isinstance(cref, dict):
        return cref
    result = dict(cref)
    result.setdefault("_class", "ChildRef")
    if isinstance(result.get("frel"), str):
        result["frel"] = _denorm_type(result["frel"], "ChildRefType")
    if isinstance(result.get("mrel"), str):
        result["mrel"] = _denorm_type(result["mrel"], "ChildRefType")
    result.setdefault("private", False)
    result.setdefault("citation_list", [])
    result.setdefault("note_list", [])
    return result


def _merge_into(base: Dict, patch: Dict, obj_type: str) -> None:
    """Apply normalised patch fields onto an existing Gramps JSON base."""
    field_map = _FIELD_PATCH_MAP.get(obj_type, {})
    for key, val in patch.items():
        if key in ("handle", "gramps_id", "change", "private"):
            continue
        gramps_key = field_map.get(key, key)
        converter = _FIELD_CONVERTERS.get((obj_type, key))
        if converter:
            base[gramps_key] = converter(val)
        elif key == "date":
            base[gramps_key] = _denorm_date(val)
        elif key in ("primary_name",):
            base[gramps_key] = _denorm_name(val)
        elif key == "event_ref_list" and isinstance(val, list):
            base[gramps_key] = [_denorm_event_ref(e) for e in val]
        elif key == "child_ref_list" and isinstance(val, list):
            base[gramps_key] = [_denorm_child_ref(c) for c in val]
        elif isinstance(val, list):
            base[gramps_key] = val  # plain handle lists: note_list, citation_list, …
        elif val is not None:
            base[gramps_key] = val


def _denorm_name(name: Dict) -> Dict:
    """Convert our name dict back to Gramps JSON name format."""
    if not isinstance(name, dict):
        return name
    result = {"_class": "Name"}
    result["first_name"] = name.get("first_name", "")
    result["suffix"] = name.get("suffix", "")
    result["title"] = name.get("title", "")
    result["call"] = name.get("call", "")
    result["nick"] = name.get("nick", "")
    result["famnick"] = name.get("famnick", "")
    result["group_as"] = name.get("group_as", "")
    result["sort_as"] = name.get("sort_as", 0)
    result["display_as"] = name.get("display_as", 0)
    result["private"] = bool(name.get("private", False))
    name_type_str = name.get("type", "Birth Name")
    result["type"] = _denorm_type(name_type_str, "NameType")
    result["date"] = _denorm_date(name.get("date", {}))
    result["citation_list"] = name.get("citation_list", [])
    result["note_list"] = name.get("note_list", [])
    surname_list = []
    for sn in name.get("surname_list", []):
        surname_list.append({
            "_class": "Surname",
            "surname": sn.get("surname", ""),
            "prefix": sn.get("prefix", ""),
            "primary": bool(sn.get("primary", True)),
            "connector": sn.get("connector", ""),
            "origintype": {"_class": "NameOriginType", "value": 1, "string": ""},
        })
    result["surname_list"] = surname_list
    return result


# Field renames: our key → Gramps JSON key (only where they differ)
_FIELD_PATCH_MAP: Dict[str, Dict[str, str]] = {
    "family": {"relationship": "type"},
}

# Per-(obj_type, field) converters
_FIELD_CONVERTERS: Dict[Tuple[str, str], Any] = {
    ("event", "type"): lambda v: _denorm_type(v, "EventType"),
    ("family", "relationship"): lambda v: _denorm_type(v, "FamilyRelType"),
    ("place", "place_type"): lambda v: _denorm_type(v, "PlaceType"),
}


def _empty_gramps_json(obj_type: str) -> Dict:
    """Return a minimal empty Gramps JSON dict for a new object."""
    templates: Dict[str, Dict] = {
        "person": {
            "_class": "Person", "gender": 2,
            "primary_name": {
                "_class": "Name", "first_name": "", "surname_list": [],
                "suffix": "", "title": "", "call": "", "nick": "",
                "famnick": "", "group_as": "", "sort_as": 0, "display_as": 0,
                "private": False, "citation_list": [], "note_list": [],
                "type": {"_class": "NameType", "value": 2, "string": ""},
                "date": _denorm_date({})
            },
            "alternate_names": [], "death_ref_index": -1, "birth_ref_index": -1,
            "event_ref_list": [], "family_list": [], "parent_family_list": [],
            "media_list": [], "address_list": [], "attribute_list": [],
            "urls": [], "lds_ord_list": [], "citation_list": [],
            "note_list": [], "tag_list": [], "person_ref_list": [],
        },
        "family": {
            "_class": "Family",
            "father_handle": None, "mother_handle": None,
            "child_ref_list": [], "event_ref_list": [], "media_list": [],
            "attribute_list": [], "lds_ord_list": [], "citation_list": [],
            "note_list": [], "tag_list": [],
            "type": {"_class": "FamilyRelType", "value": 0, "string": ""},
        },
        "event": {
            "_class": "Event",
            "type": {"_class": "EventType", "value": 12, "string": ""},
            "date": _denorm_date({}), "description": "", "place": None,
            "citation_list": [], "note_list": [], "media_list": [],
            "attribute_list": [], "tag_list": [],
        },
        "place": {
            "_class": "Place", "title": "", "long": "", "lat": "", "code": "",
            "place_type": {"_class": "PlaceType", "value": -1, "string": ""},
            "alt_names": [], "placeref_list": [],
            "name": {"_class": "PlaceName", "value": ""},
            "alt_loc": [], "urls": [], "media_list": [], "citation_list": [],
            "note_list": [], "tag_list": [], "enclosed_by": [],
        },
        "source": {
            "_class": "Source", "title": "", "author": "", "pubinfo": "",
            "abbrev": "", "note_list": [], "media_list": [], "reporef_list": [],
            "attribute_list": [], "tag_list": [], "data_maps": [],
        },
        "citation": {
            "_class": "Citation", "page": "", "confidence": 2,
            "source_handle": None, "date": _denorm_date({}),
            "note_list": [], "media_list": [], "attribute_list": [], "tag_list": [],
        },
        "note": {
            "_class": "Note", "format": 0,
            "text": {"_class": "StyledText", "string": "", "tags": []},
            "type": {"_class": "NoteType", "value": 1, "string": ""}, "tag_list": [],
        },
        "media": {
            "_class": "MediaObject", "path": "", "mime": "", "desc": "",
            "checksum": "", "date": _denorm_date({}),
            "note_list": [], "citation_list": [], "attribute_list": [],
            "tag_list": [], "media_list": [],
        },
        "repository": {
            "_class": "Repository", "name": "",
            "type": {"_class": "RepositoryType", "value": 0, "string": ""},
            "address_list": [], "urls": [], "note_list": [], "tag_list": [],
        },
    }
    return templates.get(obj_type, {"_class": obj_type.title()})


# ---------------------------------------------------------------------------
# Secondary column builders
# ---------------------------------------------------------------------------


def _secondaries(obj_type: str, obj: Dict) -> Dict[str, Any]:
    """
    Build the secondary (indexed) column values for a SQLite row.

    Args:
        obj_type: Object type string.
        obj:      Normalised dict with at least ``gramps_id`` and ``change``.

    Returns:
        Dict of column name → value for all secondary columns.
    """
    gid = obj.get("gramps_id", "")
    change = obj.get("change", int(time.time()))
    private = 1 if obj.get("private") else 0

    if obj_type == "person":
        pn = obj.get("primary_name", {})
        sl = pn.get("surname_list", [])
        return {
            "gramps_id": gid, "gender": obj.get("gender", 2),
            "given_name": pn.get("first_name", ""),
            "surname": sl[0].get("surname", "") if sl else "",
            "birth_ref_index": obj.get("birth_ref_index", -1),
            "death_ref_index": obj.get("death_ref_index", -1),
            "change": change, "private": private,
        }
    if obj_type == "family":
        return {
            "gramps_id": gid,
            "father_handle": obj.get("father_handle") or None,
            "mother_handle": obj.get("mother_handle") or None,
            "change": change, "private": private,
        }
    if obj_type == "event":
        return {
            "gramps_id": gid, "description": obj.get("description", ""),
            "place": obj.get("place") or None,
            "change": change, "private": private,
        }
    if obj_type == "place":
        return {
            "gramps_id": gid, "title": obj.get("title", ""),
            "long": obj.get("long", ""), "lat": obj.get("lat", ""),
            "code": obj.get("code", ""),
            "enclosed_by": (obj.get("placeref_list") or [{}])[0].get("ref") or None
            if obj.get("placeref_list") else None,
            "change": change, "private": private,
        }
    if obj_type == "source":
        return {
            "gramps_id": gid, "title": obj.get("title", ""),
            "author": obj.get("author", ""), "pubinfo": obj.get("pubinfo", ""),
            "abbrev": obj.get("abbrev", ""),
            "change": change, "private": private,
        }
    if obj_type == "citation":
        return {
            "gramps_id": gid, "page": obj.get("page", ""),
            "confidence": obj.get("confidence", 2),
            "source_handle": obj.get("source_handle") or None,
            "change": change, "private": private,
        }
    if obj_type == "note":
        return {
            "gramps_id": gid,
            "format": 1 if obj.get("format") else 0,
            "change": change, "private": private,
        }
    if obj_type == "media":
        return {
            "gramps_id": gid, "path": obj.get("path", ""),
            "mime": obj.get("mime", ""), "desc": obj.get("desc", ""),
            "checksum": obj.get("checksum", ""),
            "change": change, "private": private,
        }
    if obj_type == "repository":
        return {
            "gramps_id": gid, "name": obj.get("name", ""),
            "change": change, "private": private,
        }
    return {"gramps_id": gid, "change": change}
