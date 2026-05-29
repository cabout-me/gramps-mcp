"""
Shared pytest fixtures for GrampsSqliteClient tests.

Creates an in-memory SQLite database with the Gramps schema and populates
it with the same synthetic test data used for the XML direct-client tests,
serialised as Gramps-format JSON.
"""

import json
import sqlite3
import time

import pytest

from gramps_mcp._gramps_sqlite import GrampsSqliteDB, _load_sqlite, _denorm_date

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE person (
    handle VARCHAR(50) PRIMARY KEY NOT NULL,
    given_name TEXT, surname TEXT,
    json_data TEXT,
    gramps_id TEXT, gender INTEGER,
    death_ref_index INTEGER DEFAULT -1,
    birth_ref_index INTEGER DEFAULT -1,
    change INTEGER DEFAULT 0, private INTEGER DEFAULT 0
);
CREATE TABLE family (
    handle VARCHAR(50) PRIMARY KEY NOT NULL,
    json_data TEXT, gramps_id TEXT,
    father_handle VARCHAR(50), mother_handle VARCHAR(50),
    change INTEGER DEFAULT 0, private INTEGER DEFAULT 0
);
CREATE TABLE event (
    handle VARCHAR(50) PRIMARY KEY NOT NULL,
    json_data TEXT, gramps_id TEXT,
    description TEXT, place VARCHAR(50),
    change INTEGER DEFAULT 0, private INTEGER DEFAULT 0
);
CREATE TABLE place (
    handle VARCHAR(50) PRIMARY KEY NOT NULL,
    json_data TEXT, gramps_id TEXT,
    title TEXT, long TEXT, lat TEXT, code TEXT, enclosed_by VARCHAR(50),
    change INTEGER DEFAULT 0, private INTEGER DEFAULT 0
);
CREATE TABLE source (
    handle VARCHAR(50) PRIMARY KEY NOT NULL,
    json_data TEXT, gramps_id TEXT,
    title TEXT, author TEXT, pubinfo TEXT, abbrev TEXT,
    change INTEGER DEFAULT 0, private INTEGER DEFAULT 0
);
CREATE TABLE citation (
    handle VARCHAR(50) PRIMARY KEY NOT NULL,
    json_data TEXT, gramps_id TEXT,
    page TEXT, confidence INTEGER DEFAULT 2,
    source_handle VARCHAR(50),
    change INTEGER DEFAULT 0, private INTEGER DEFAULT 0
);
CREATE TABLE note (
    handle VARCHAR(50) PRIMARY KEY NOT NULL,
    json_data TEXT, gramps_id TEXT,
    format INTEGER DEFAULT 0,
    change INTEGER DEFAULT 0, private INTEGER DEFAULT 0
);
CREATE TABLE media (
    handle VARCHAR(50) PRIMARY KEY NOT NULL,
    json_data TEXT, gramps_id TEXT,
    path TEXT, mime TEXT, desc TEXT, checksum TEXT,
    change INTEGER DEFAULT 0, private INTEGER DEFAULT 0
);
CREATE TABLE repository (
    handle VARCHAR(50) PRIMARY KEY NOT NULL,
    json_data TEXT, gramps_id TEXT, name TEXT,
    change INTEGER DEFAULT 0, private INTEGER DEFAULT 0
);
CREATE TABLE tag (
    handle VARCHAR(50) PRIMARY KEY NOT NULL,
    json_data TEXT, name TEXT, color VARCHAR(13),
    priority INTEGER DEFAULT 0, change INTEGER DEFAULT 0
);
CREATE TABLE reference (
    obj_handle VARCHAR(50), obj_class TEXT,
    ref_handle VARCHAR(50), ref_class TEXT
);
CREATE TABLE metadata (
    setting VARCHAR(50) PRIMARY KEY NOT NULL,
    json_data TEXT, value BLOB
);
"""

# ---------------------------------------------------------------------------
# Test data — Gramps JSON format
# ---------------------------------------------------------------------------

_BIRTH_DATE = {"_class": "Date", "calendar": 0, "modifier": 0, "quality": 0,
               "dateval": [15, 6, 1950, False], "text": "", "sortval": 0,
               "newyear": 0, "format": None}
_DEATH_DATE = {"_class": "Date", "calendar": 0, "modifier": 3, "quality": 1,
               "dateval": [1, 3, 2020, False], "text": "", "sortval": 0,
               "newyear": 0, "format": None}
_BIRTH_JANE = {"_class": "Date", "calendar": 0, "modifier": 0, "quality": 0,
               "dateval": [30, 11, 1952, False], "text": "", "sortval": 0,
               "newyear": 0, "format": None}
_MARRIAGE_DATE = {"_class": "Date", "calendar": 0, "modifier": 0, "quality": 0,
                  "dateval": [20, 4, 1975, False], "text": "", "sortval": 0,
                  "newyear": 0, "format": None}
_EMPTY_DATE = _denorm_date({})


def _name(first, surname, name_type=2):
    return {
        "_class": "Name",
        "first_name": first,
        "surname_list": [{"_class": "Surname", "surname": surname, "prefix": "",
                          "primary": True, "connector": "",
                          "origintype": {"_class": "NameOriginType", "value": 1, "string": ""}}],
        "suffix": "", "title": "", "call": "", "nick": "", "famnick": "",
        "group_as": "", "sort_as": 0, "display_as": 0, "private": False,
        "citation_list": [], "note_list": [],
        "type": {"_class": "NameType", "value": name_type, "string": ""},
        "date": _EMPTY_DATE,
    }


def _eref(handle, role_val=1):
    return {"_class": "EventRef", "ref": handle,
            "role": {"_class": "EventRoleType", "value": role_val, "string": ""},
            "note_list": [], "attribute_list": [], "private": False}


def _cref(handle):
    return {"_class": "ChildRef", "ref": handle,
            "frel": {"_class": "ChildRefType", "value": 1, "string": ""},
            "mrel": {"_class": "ChildRefType", "value": 1, "string": ""},
            "private": False, "citation_list": [], "note_list": []}


PEOPLE = [
    # I0001 — John Robert Smith
    ("h_pe_john", "I0001", {
        "_class": "Person", "handle": "h_pe_john", "gramps_id": "I0001",
        "gender": 1,
        "primary_name": _name("John Robert", "Smith"),
        "alternate_names": [], "death_ref_index": 1, "birth_ref_index": 0,
        "event_ref_list": [_eref("h_ev_birth_john"), _eref("h_ev_death_john")],
        "family_list": ["h_fa_smith"], "parent_family_list": [],
        "media_list": [{"_class": "MediaRef", "ref": "h_me_photo", "rect": None,
                        "private": False, "note_list": [], "attribute_list": [], "citation_list": []}],
        "address_list": [], "attribute_list": [],
        "urls": [{"_class": "Url", "path": "https://example.com/john",
                  "description": "Homepage", "type": {"_class": "UrlType", "value": 0, "string": "Web Home"},
                  "private": False}],
        "lds_ord_list": [], "citation_list": ["h_ci_birth"],
        "note_list": ["h_no_john"], "tag_list": [], "person_ref_list": [],
        "change": 0, "private": False,
    }),
    # I0002 — Jane Doe
    ("h_pe_jane", "I0002", {
        "_class": "Person", "handle": "h_pe_jane", "gramps_id": "I0002",
        "gender": 0,
        "primary_name": _name("Jane", "Doe"),
        "alternate_names": [], "death_ref_index": -1, "birth_ref_index": 0,
        "event_ref_list": [_eref("h_ev_birth_jane")],
        "family_list": ["h_fa_smith"], "parent_family_list": [],
        "media_list": [], "address_list": [], "attribute_list": [], "urls": [],
        "lds_ord_list": [], "citation_list": [], "note_list": [], "tag_list": [],
        "person_ref_list": [], "change": 0, "private": False,
    }),
    # I0003 — James Smith (child)
    ("h_pe_child", "I0003", {
        "_class": "Person", "handle": "h_pe_child", "gramps_id": "I0003",
        "gender": 1,
        "primary_name": _name("James", "Smith"),
        "alternate_names": [], "death_ref_index": -1, "birth_ref_index": 0,
        "event_ref_list": [_eref("h_ev_birth_child")],
        "family_list": [], "parent_family_list": ["h_fa_smith"],
        "media_list": [], "address_list": [], "attribute_list": [], "urls": [],
        "lds_ord_list": [], "citation_list": [], "note_list": [], "tag_list": [],
        "person_ref_list": [], "change": 0, "private": False,
    }),
]

EVENTS = [
    ("h_ev_birth_john", "E0001", {
        "_class": "Event", "handle": "h_ev_birth_john", "gramps_id": "E0001",
        "type": {"_class": "EventType", "value": 12, "string": ""},
        "date": _BIRTH_DATE, "description": "", "place": "h_pl_berlin",
        "citation_list": [], "note_list": [], "media_list": [],
        "attribute_list": [], "tag_list": [], "change": 0, "private": False,
    }),
    ("h_ev_death_john", "E0002", {
        "_class": "Event", "handle": "h_ev_death_john", "gramps_id": "E0002",
        "type": {"_class": "EventType", "value": 13, "string": ""},
        "date": _DEATH_DATE, "description": "", "place": "h_pl_hamburg",
        "citation_list": [], "note_list": [], "media_list": [],
        "attribute_list": [], "tag_list": [], "change": 0, "private": False,
    }),
    ("h_ev_birth_jane", "E0003", {
        "_class": "Event", "handle": "h_ev_birth_jane", "gramps_id": "E0003",
        "type": {"_class": "EventType", "value": 12, "string": ""},
        "date": _BIRTH_JANE, "description": "", "place": None,
        "citation_list": [], "note_list": [], "media_list": [],
        "attribute_list": [], "tag_list": [], "change": 0, "private": False,
    }),
    ("h_ev_marriage", "E0004", {
        "_class": "Event", "handle": "h_ev_marriage", "gramps_id": "E0004",
        "type": {"_class": "EventType", "value": 1, "string": ""},
        "date": _MARRIAGE_DATE, "description": "", "place": "h_pl_berlin",
        "citation_list": [], "note_list": [], "media_list": [],
        "attribute_list": [], "tag_list": [], "change": 0, "private": False,
    }),
    ("h_ev_birth_child", "E0005", {
        "_class": "Event", "handle": "h_ev_birth_child", "gramps_id": "E0005",
        "type": {"_class": "EventType", "value": 12, "string": ""},
        "date": _EMPTY_DATE, "description": "", "place": None,
        "citation_list": [], "note_list": [], "media_list": [],
        "attribute_list": [], "tag_list": [], "change": 0, "private": False,
    }),
]

FAMILIES = [
    ("h_fa_smith", "F0001", {
        "_class": "Family", "handle": "h_fa_smith", "gramps_id": "F0001",
        "father_handle": "h_pe_john", "mother_handle": "h_pe_jane",
        "child_ref_list": [_cref("h_pe_child")],
        "type": {"_class": "FamilyRelType", "value": 0, "string": ""},
        "event_ref_list": [_eref("h_ev_marriage", role_val=8)],
        "media_list": [], "attribute_list": [], "lds_ord_list": [],
        "citation_list": [], "note_list": ["h_no_john"], "tag_list": [],
        "change": 0, "private": False,
    }),
]

PLACES = [
    ("h_pl_berlin", "P0001", {
        "_class": "Place", "handle": "h_pl_berlin", "gramps_id": "P0001",
        "title": "Berlin, Germany",
        "place_type": {"_class": "PlaceType", "value": 4, "string": ""},
        "name": {"_class": "PlaceName", "value": "Berlin", "date": _EMPTY_DATE, "lang": ""},
        "alt_names": [], "placeref_list": [], "long": "", "lat": "", "code": "",
        "alt_loc": [], "urls": [{"_class": "Url", "path": "https://en.wikipedia.org/wiki/Berlin",
                                  "description": "", "type": {"_class": "UrlType", "value": 0, "string": "Web Home"},
                                  "private": False}],
        "media_list": [], "citation_list": [], "note_list": [], "tag_list": [],
        "enclosed_by": [], "change": 0, "private": False,
    }),
    ("h_pl_hamburg", "P0002", {
        "_class": "Place", "handle": "h_pl_hamburg", "gramps_id": "P0002",
        "title": "Hamburg, Germany",
        "place_type": {"_class": "PlaceType", "value": 4, "string": ""},
        "name": {"_class": "PlaceName", "value": "Hamburg", "date": _EMPTY_DATE, "lang": ""},
        "alt_names": [], "placeref_list": [{"_class": "PlaceRef", "ref": "h_pl_germany", "date": _EMPTY_DATE}],
        "long": "", "lat": "", "code": "", "alt_loc": [], "urls": [],
        "media_list": [], "citation_list": [], "note_list": [], "tag_list": [],
        "enclosed_by": [], "change": 0, "private": False,
    }),
]

SOURCES = [
    ("h_so_civil", "S0001", {
        "_class": "Source", "handle": "h_so_civil", "gramps_id": "S0001",
        "title": "Civil Records Office", "author": "State Archive",
        "pubinfo": "Berlin, 1950", "abbrev": "CRO",
        "note_list": [], "media_list": [], "reporef_list": [
            {"_class": "RepoRef", "ref": "h_re_archive", "callno": "Vol. 3",
             "medium": {"_class": "SourceMediaType", "value": 0, "string": "Book"},
             "note_list": [], "private": False}
        ],
        "attribute_list": [], "tag_list": [], "data_maps": [],
        "change": 0, "private": False,
    }),
]

CITATIONS = [
    ("h_ci_birth", "C0001", {
        "_class": "Citation", "handle": "h_ci_birth", "gramps_id": "C0001",
        "page": "Certificate No. 12345", "confidence": 2,
        "source_handle": "h_so_civil",
        "date": {"_class": "Date", "calendar": 0, "modifier": 0, "quality": 0,
                 "dateval": [15, 1, 2024, False], "text": "", "sortval": 0,
                 "newyear": 0, "format": None},
        "note_list": ["h_no_john"], "media_list": [], "attribute_list": [],
        "tag_list": [], "change": 0, "private": False,
    }),
]

NOTES = [
    ("h_no_john", "N0001", {
        "_class": "Note", "handle": "h_no_john", "gramps_id": "N0001",
        "format": 0,
        "text": {"_class": "StyledText",
                 "string": "John Smith was a notable person in his community.",
                 "tags": []},
        "type": {"_class": "NoteType", "value": 1, "string": "General"},
        "tag_list": [], "change": 0, "private": False,
    }),
]

MEDIA = [
    ("h_me_photo", "O0001", {
        "_class": "MediaObject", "handle": "h_me_photo", "gramps_id": "O0001",
        "path": "/photos/family.jpg", "mime": "image/jpeg",
        "desc": "Family photo 1975", "checksum": "abc123def456",
        "date": _EMPTY_DATE,
        "note_list": [], "citation_list": [], "attribute_list": [],
        "tag_list": [], "media_list": [], "change": 0, "private": False,
    }),
]

REPOSITORIES = [
    ("h_re_archive", "R0001", {
        "_class": "Repository", "handle": "h_re_archive", "gramps_id": "R0001",
        "name": "State Archive Berlin",
        "type": {"_class": "RepositoryType", "value": 2, "string": ""},
        "address_list": [],
        "urls": [{"_class": "Url", "path": "https://archive.berlin.de",
                  "description": "", "type": {"_class": "UrlType", "value": 0, "string": "Web Home"},
                  "private": False}],
        "note_list": [], "tag_list": [], "change": 0, "private": False,
    }),
]


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_in_memory_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)

    def _ins(table, rows, extra_cols, extra_fn):
        for row in rows:
            handle, gid, data = row
            extras = extra_fn(data)
            cols = ["handle", "gramps_id", "json_data"] + extra_cols
            vals = [handle, gid, json.dumps(data, ensure_ascii=False)] + extras
            placeholders = ",".join("?" * len(cols))
            conn.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})", vals)

    # People
    for handle, gid, data in PEOPLE:
        pn = data.get("primary_name", {})
        sl = pn.get("surname_list", [])
        conn.execute(
            "INSERT INTO person (handle,gramps_id,json_data,given_name,surname,"
            "gender,birth_ref_index,death_ref_index,change,private) VALUES (?,?,?,?,?,?,?,?,?,?)",
            [handle, gid, json.dumps(data), pn.get("first_name", ""),
             sl[0]["surname"] if sl else "",
             data["gender"], data["birth_ref_index"], data["death_ref_index"], 0, 0]
        )

    # Events
    for handle, gid, data in EVENTS:
        conn.execute(
            "INSERT INTO event (handle,gramps_id,json_data,description,place,change,private) "
            "VALUES (?,?,?,?,?,?,?)",
            [handle, gid, json.dumps(data), data.get("description", ""),
             data.get("place"), 0, 0]
        )

    # Families
    for handle, gid, data in FAMILIES:
        conn.execute(
            "INSERT INTO family (handle,gramps_id,json_data,father_handle,mother_handle,change,private) "
            "VALUES (?,?,?,?,?,?,?)",
            [handle, gid, json.dumps(data), data.get("father_handle"),
             data.get("mother_handle"), 0, 0]
        )

    # Places
    for handle, gid, data in PLACES:
        conn.execute(
            "INSERT INTO place (handle,gramps_id,json_data,title,change,private) VALUES (?,?,?,?,?,?)",
            [handle, gid, json.dumps(data), data.get("title", ""), 0, 0]
        )

    # Sources
    for handle, gid, data in SOURCES:
        conn.execute(
            "INSERT INTO source (handle,gramps_id,json_data,title,author,pubinfo,abbrev,change,private) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            [handle, gid, json.dumps(data), data["title"], data["author"],
             data["pubinfo"], data["abbrev"], 0, 0]
        )

    # Citations
    for handle, gid, data in CITATIONS:
        conn.execute(
            "INSERT INTO citation (handle,gramps_id,json_data,page,confidence,source_handle,change,private) "
            "VALUES (?,?,?,?,?,?,?,?)",
            [handle, gid, json.dumps(data), data["page"], data["confidence"],
             data["source_handle"], 0, 0]
        )

    # Notes
    for handle, gid, data in NOTES:
        conn.execute(
            "INSERT INTO note (handle,gramps_id,json_data,format,change,private) VALUES (?,?,?,?,?,?)",
            [handle, gid, json.dumps(data), data["format"], 0, 0]
        )

    # Media
    for handle, gid, data in MEDIA:
        conn.execute(
            "INSERT INTO media (handle,gramps_id,json_data,path,mime,desc,checksum,change,private) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            [handle, gid, json.dumps(data), data["path"], data["mime"],
             data["desc"], data["checksum"], 0, 0]
        )

    # Repositories
    for handle, gid, data in REPOSITORIES:
        conn.execute(
            "INSERT INTO repository (handle,gramps_id,json_data,name,change,private) VALUES (?,?,?,?,?,?)",
            [handle, gid, json.dumps(data), data["name"], 0, 0]
        )

    conn.commit()
    return conn


@pytest.fixture(scope="session")
def sqlite_conn():
    """In-memory SQLite connection loaded with synthetic Gramps data."""
    return _make_in_memory_db()


@pytest.fixture(scope="session")
def sqlite_db(sqlite_conn):
    """GrampsSqliteDB backed by the in-memory fixture (lazy-loading)."""
    from gramps_mcp._gramps_sqlite import GrampsSqliteDB
    return GrampsSqliteDB(conn=sqlite_conn, db_path=":memory:", read_only=False)


@pytest.fixture(scope="session")
def sqlite_client(sqlite_db):
    """GrampsSqliteClient wrapping the in-memory fixture DB."""
    from gramps_mcp.sqlite_client import GrampsSqliteClient
    client = object.__new__(GrampsSqliteClient)
    client._db = sqlite_db
    client._db_path = ":memory:"
    client._report_cache = {}
    return client
