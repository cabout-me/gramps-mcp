"""
Tests for GrampsSqliteClient — full read/write Gramps SQLite backend.

All tests use the synthetic in-memory fixture from conftest_sqlite.py.
No real Gramps database, no GTK, no external server required.

Run with:
    uv run pytest tests/test_sqlite_client.py -v
"""

import pytest

from gramps_mcp.client import GrampsAPIError
from gramps_mcp.models.api_calls import ApiCalls

# Fixtures from conftest_sqlite.py are auto-discovered by pytest


# ===========================================================================
# Normalisation: types become plain strings
# ===========================================================================


class TestNormalisation:
    def test_event_type_is_string(self, sqlite_db):
        ev = sqlite_db.get("event", "h_ev_birth_john")
        assert ev["type"] == "Birth"

    def test_death_type_is_string(self, sqlite_db):
        ev = sqlite_db.get("event", "h_ev_death_john")
        assert ev["type"] == "Death"

    def test_marriage_type_is_string(self, sqlite_db):
        ev = sqlite_db.get("event", "h_ev_marriage")
        assert ev["type"] == "Marriage"

    def test_family_has_relationship_not_type(self, sqlite_db):
        fam = sqlite_db.get("family", "h_fa_smith")
        assert "relationship" in fam
        assert fam["relationship"] == "Married"
        assert "type" not in fam

    def test_date_has_string_not_text(self, sqlite_db):
        ev = sqlite_db.get("event", "h_ev_birth_john")
        date = ev["date"]
        assert "string" in date
        assert "text" not in date

    def test_date_dateval(self, sqlite_db):
        ev = sqlite_db.get("event", "h_ev_birth_john")
        assert ev["date"]["dateval"] == [15, 6, 1950, False]

    def test_no_class_keys_in_person(self, sqlite_db):
        person = sqlite_db.get("person", "h_pe_john")
        assert "_class" not in person
        assert "_class" not in person["primary_name"]

    def test_event_ref_role_is_string(self, sqlite_db):
        person = sqlite_db.get("person", "h_pe_john")
        role = person["event_ref_list"][0]["role"]
        assert isinstance(role, str)
        assert role == "Primary"

    def test_child_ref_frel_is_string(self, sqlite_db):
        fam = sqlite_db.get("family", "h_fa_smith")
        frel = fam["child_ref_list"][0]["frel"]
        assert isinstance(frel, str)
        assert frel == "Birth"


# ===========================================================================
# Read: persons
# ===========================================================================


class TestReadPerson:
    def test_get_by_handle(self, sqlite_db):
        p = sqlite_db.get("person", "h_pe_john")
        assert p["gramps_id"] == "I0001"
        assert p["handle"] == "h_pe_john"

    def test_get_by_gramps_id(self, sqlite_db):
        p = sqlite_db.get_by_id("person", "I0001")
        assert p is not None
        assert p["handle"] == "h_pe_john"

    def test_missing_returns_none(self, sqlite_db):
        assert sqlite_db.get("person", "no_such_handle") is None

    def test_person_name(self, sqlite_db):
        pn = sqlite_db.get("person", "h_pe_john")["primary_name"]
        assert pn["first_name"] == "John Robert"
        assert pn["surname_list"][0]["surname"] == "Smith"

    def test_person_gender(self, sqlite_db):
        assert sqlite_db.get("person", "h_pe_john")["gender"] == 1
        assert sqlite_db.get("person", "h_pe_jane")["gender"] == 0

    def test_birth_ref_index(self, sqlite_db):
        p = sqlite_db.get("person", "h_pe_john")
        assert p["birth_ref_index"] == 0
        assert p["event_ref_list"][0]["ref"] == "h_ev_birth_john"

    def test_death_ref_index(self, sqlite_db):
        assert sqlite_db.get("person", "h_pe_john")["death_ref_index"] == 1

    def test_no_death_for_jane(self, sqlite_db):
        assert sqlite_db.get("person", "h_pe_jane")["death_ref_index"] == -1

    def test_family_list(self, sqlite_db):
        p = sqlite_db.get("person", "h_pe_john")
        assert "h_fa_smith" in p["family_list"]

    def test_parent_family_list(self, sqlite_db):
        child = sqlite_db.get("person", "h_pe_child")
        assert "h_fa_smith" in child["parent_family_list"]

    def test_media_list(self, sqlite_db):
        media = sqlite_db.get("person", "h_pe_john")["media_list"]
        assert len(media) == 1
        assert media[0]["ref"] == "h_me_photo"

    def test_count(self, sqlite_db):
        assert sqlite_db.count("person") == 3

    def test_all(self, sqlite_db):
        assert len(sqlite_db.all("person")) == 3


# ===========================================================================
# Read: events, families, places
# ===========================================================================


class TestReadEvent:
    def test_event_place_handle(self, sqlite_db):
        ev = sqlite_db.get("event", "h_ev_birth_john")
        assert ev["place"] == "h_pl_berlin"

    def test_event_no_place(self, sqlite_db):
        ev = sqlite_db.get("event", "h_ev_birth_jane")
        assert not ev["place"]

    def test_event_count(self, sqlite_db):
        assert sqlite_db.count("event") == 5


class TestReadFamily:
    def test_parents(self, sqlite_db):
        fam = sqlite_db.get("family", "h_fa_smith")
        assert fam["father_handle"] == "h_pe_john"
        assert fam["mother_handle"] == "h_pe_jane"

    def test_children(self, sqlite_db):
        refs = sqlite_db.get("family", "h_fa_smith")["child_ref_list"]
        assert len(refs) == 1
        assert refs[0]["ref"] == "h_pe_child"


class TestReadPlace:
    def test_place_title(self, sqlite_db):
        p = sqlite_db.get("place", "h_pl_berlin")
        assert p["title"] == "Berlin, Germany"

    def test_place_type(self, sqlite_db):
        p = sqlite_db.get("place", "h_pl_berlin")
        assert p["place_type"] == "City"


# ===========================================================================
# API: make_api_call  (read)
# ===========================================================================


class TestApiRead:
    @pytest.mark.asyncio
    async def test_get_person(self, sqlite_client):
        p = await sqlite_client.make_api_call(ApiCalls.GET_PERSON, handle="h_pe_john")
        assert p["gramps_id"] == "I0001"

    @pytest.mark.asyncio
    async def test_get_person_extended(self, sqlite_client):
        p = await sqlite_client.make_api_call(
            ApiCalls.GET_PERSON, params={"extend": "all"}, handle="h_pe_john"
        )
        ext = p["extended"]
        assert len(ext["events"]) == 2
        assert len(ext["families"]) == 1

    @pytest.mark.asyncio
    async def test_get_family_extended(self, sqlite_client):
        fam = await sqlite_client.make_api_call(
            ApiCalls.GET_FAMILY, params={"extend": "all"}, handle="h_fa_smith"
        )
        ext = fam["extended"]
        assert ext["father"]["gramps_id"] == "I0001"
        assert ext["mother"]["gramps_id"] == "I0002"
        assert len(ext["children"]) == 1

    @pytest.mark.asyncio
    async def test_missing_handle_raises(self, sqlite_client):
        with pytest.raises(GrampsAPIError, match="not found"):
            await sqlite_client.make_api_call(ApiCalls.GET_PERSON, handle="nope")

    @pytest.mark.asyncio
    async def test_list_people(self, sqlite_client):
        people = await sqlite_client.make_api_call(
            ApiCalls.GET_PEOPLE, params={"pagesize": 100}
        )
        assert len(people) == 3

    @pytest.mark.asyncio
    async def test_filter_by_gramps_id(self, sqlite_client):
        result = await sqlite_client.make_api_call(
            ApiCalls.GET_PEOPLE, params={"gramps_id": "I0001"}
        )
        assert len(result) == 1
        assert result[0]["handle"] == "h_pe_john"

    @pytest.mark.asyncio
    async def test_name_search(self, sqlite_client):
        result = await sqlite_client.make_api_call(
            ApiCalls.GET_PEOPLE, params={"query": "smith", "pagesize": 20}
        )
        ids = {p["gramps_id"] for p in result}
        assert "I0001" in ids
        assert "I0003" in ids

    @pytest.mark.asyncio
    async def test_gql_filter(self, sqlite_client):
        result = await sqlite_client.make_api_call(
            ApiCalls.GET_PEOPLE, params={"gql": "gender = 1", "pagesize": 100}
        )
        assert all(p["gender"] == 1 for p in result)

    @pytest.mark.asyncio
    async def test_tree_info(self, sqlite_client):
        info = await sqlite_client.make_api_call(ApiCalls.GET_TREE)
        assert info["usage_people"] == 3
        assert info["usage_events"] == 5
        assert info["usage_families"] == 1

    @pytest.mark.asyncio
    async def test_with_headers(self, sqlite_client):
        result, headers = await sqlite_client.make_api_call(
            ApiCalls.GET_PEOPLE, params={"pagesize": 100}, with_headers=True
        )
        assert len(result) == 3
        assert headers["x-total-count"] == "3"


# ===========================================================================
# API: make_api_call  (write)
# ===========================================================================


class TestApiWrite:
    @pytest.mark.asyncio
    async def test_create_person(self, sqlite_client):
        new_person = {
            "gender": 0,
            "primary_name": {
                "first_name": "Anna",
                "surname_list": [{"surname": "Müller", "primary": True,
                                   "prefix": "", "connector": ""}],
                "suffix": "", "title": "", "call": "", "nick": "",
                "type": "Birth Name",
            },
            "event_ref_list": [],
            "family_list": [], "parent_family_list": [],
            "note_list": [], "citation_list": [], "media_list": [],
            "address_list": [], "urls": [],
        }
        result = await sqlite_client.make_api_call(ApiCalls.POST_PEOPLE, params=new_person)
        assert "handle" in result
        assert result["gramps_id"] != ""
        assert result["gender"] == 0
        # Verify it's retrievable
        fetched = await sqlite_client.make_api_call(
            ApiCalls.GET_PERSON, handle=result["handle"]
        )
        assert fetched["primary_name"]["first_name"] == "Anna"

    @pytest.mark.asyncio
    async def test_update_person_gender(self, sqlite_client):
        # Create a person to update
        new_p = await sqlite_client.make_api_call(ApiCalls.POST_PEOPLE, params={
            "gender": 1,
            "primary_name": {"first_name": "Karl", "surname_list": [
                {"surname": "Test", "primary": True, "prefix": "", "connector": ""}
            ], "suffix": "", "title": "", "call": "", "nick": "", "type": "Birth Name"},
            "event_ref_list": [], "family_list": [], "parent_family_list": [],
            "note_list": [], "citation_list": [], "media_list": [],
            "address_list": [], "urls": [],
        })
        handle = new_p["handle"]
        updated = await sqlite_client.make_api_call(
            ApiCalls.PUT_PERSON, params={"gender": 0}, handle=handle
        )
        assert updated["gender"] == 0
        fetched = await sqlite_client.make_api_call(ApiCalls.GET_PERSON, handle=handle)
        assert fetched["gender"] == 0

    @pytest.mark.asyncio
    async def test_create_event(self, sqlite_client):
        new_event = {
            "type": "Baptism",
            "date": {"dateval": [5, 3, 1951, False], "modifier": 0,
                     "quality": 0, "string": ""},
            "description": "Baptism at St. Mary's",
            "place": "h_pl_berlin",
            "note_list": [], "citation_list": [],
        }
        result = await sqlite_client.make_api_call(ApiCalls.POST_EVENTS, params=new_event)
        assert result["gramps_id"].startswith("E")
        fetched = await sqlite_client.make_api_call(
            ApiCalls.GET_EVENT, handle=result["handle"]
        )
        assert fetched["type"] == "Baptism"
        assert fetched["description"] == "Baptism at St. Mary's"

    @pytest.mark.asyncio
    async def test_create_note(self, sqlite_client):
        new_note = {
            "type": "General",
            "text": {"string": "Research note about John Smith's origins."},
        }
        result = await sqlite_client.make_api_call(ApiCalls.POST_NOTES, params=new_note)
        assert result["gramps_id"].startswith("N")
        fetched = await sqlite_client.make_api_call(
            ApiCalls.GET_NOTE, handle=result["handle"]
        )
        text = fetched.get("text", {})
        if isinstance(text, dict):
            assert "Smith" in text.get("string", "")
        else:
            assert "Smith" in str(text)

    @pytest.mark.asyncio
    async def test_new_handle_is_unique(self, sqlite_client):
        h1 = sqlite_client._db.new_handle()
        h2 = sqlite_client._db.new_handle()
        assert h1 != h2

    @pytest.mark.asyncio
    async def test_gramps_id_increments(self, sqlite_client):
        p1 = await sqlite_client.make_api_call(ApiCalls.POST_PEOPLE, params={
            "gender": 2,
            "primary_name": {"first_name": "X", "surname_list": [
                {"surname": "Y", "primary": True, "prefix": "", "connector": ""}
            ], "suffix": "", "title": "", "call": "", "nick": "", "type": "Birth Name"},
            "event_ref_list": [], "family_list": [], "parent_family_list": [],
            "note_list": [], "citation_list": [], "media_list": [],
            "address_list": [], "urls": [],
        })
        p2 = await sqlite_client.make_api_call(ApiCalls.POST_PEOPLE, params={
            "gender": 2,
            "primary_name": {"first_name": "A", "surname_list": [
                {"surname": "B", "primary": True, "prefix": "", "connector": ""}
            ], "suffix": "", "title": "", "call": "", "nick": "", "type": "Birth Name"},
            "event_ref_list": [], "family_list": [], "parent_family_list": [],
            "note_list": [], "citation_list": [], "media_list": [],
            "address_list": [], "urls": [],
        })
        n1 = int(p1["gramps_id"][1:])
        n2 = int(p2["gramps_id"][1:])
        assert n2 == n1 + 1


# ===========================================================================
# Timelines
# ===========================================================================


class TestTimeline:
    @pytest.mark.asyncio
    async def test_person_timeline_is_list(self, sqlite_client):
        result = await sqlite_client.make_api_call(
            ApiCalls.GET_PERSON_TIMELINE, handle="h_pe_john"
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_person_timeline_has_birth(self, sqlite_client):
        result = await sqlite_client.make_api_call(
            ApiCalls.GET_PERSON_TIMELINE, handle="h_pe_john"
        )
        types = {e["type"] for e in result}
        assert "Birth" in types

    @pytest.mark.asyncio
    async def test_person_timeline_includes_marriage(self, sqlite_client):
        result = await sqlite_client.make_api_call(
            ApiCalls.GET_PERSON_TIMELINE, handle="h_pe_john"
        )
        types = {e["type"] for e in result}
        assert "Marriage" in types

    @pytest.mark.asyncio
    async def test_family_timeline(self, sqlite_client):
        result = await sqlite_client.make_api_call(
            ApiCalls.GET_FAMILY_TIMELINE, handle="h_fa_smith"
        )
        assert isinstance(result, list)
        assert len(result) >= 1


# ===========================================================================
# Client factory: auto-detection
# ===========================================================================


class TestReadOnlyMode:
    def test_read_only_flag_stored(self, sqlite_db):
        from gramps_mcp._gramps_sqlite import GrampsSqliteDB
        assert hasattr(sqlite_db, "_read_only")

    @pytest.mark.asyncio
    async def test_put_raises_when_read_only(self, tmp_path):
        """Writing to a read-only DB raises GrampsAPIError."""
        import sqlite3
        from gramps_mcp._gramps_sqlite import _load_sqlite
        # Create a minimal empty SQLite file
        db_path = tmp_path / "ro_test.sqlite"
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "CREATE TABLE person (handle TEXT PRIMARY KEY, gramps_id TEXT, "
            "json_data TEXT, given_name TEXT, surname TEXT, gender INTEGER, "
            "birth_ref_index INTEGER DEFAULT -1, death_ref_index INTEGER DEFAULT -1, "
            "change INTEGER DEFAULT 0, private INTEGER DEFAULT 0)"
        )
        conn.commit()
        conn.close()

        db = _load_sqlite(str(db_path), read_only=True)
        with pytest.raises(GrampsAPIError, match="read-only"):
            db.put("person", {"gender": 1, "primary_name": {
                "first_name": "Test",
                "surname_list": [{"surname": "X", "primary": True,
                                   "prefix": "", "connector": ""}],
            }})
        db.close()


class TestClientFactory:
    def test_sqlite_path_detected(self, tmp_path):
        from gramps_mcp.client import _is_sqlite_path
        db = tmp_path / "sqlite.db"
        db.write_bytes(b"")
        assert _is_sqlite_path(str(db))

    def test_gpkg_not_sqlite(self):
        from gramps_mcp.client import _is_sqlite_path
        assert not _is_sqlite_path("/some/path/tree.gpkg")

    def test_directory_with_sqlite_db(self, tmp_path):
        from gramps_mcp.client import _is_sqlite_path
        (tmp_path / "sqlite.db").write_bytes(b"")
        assert _is_sqlite_path(str(tmp_path))

    def test_gramps_file_not_sqlite(self):
        from gramps_mcp.client import _is_sqlite_path
        assert not _is_sqlite_path("/some/path/tree.gramps")


class TestSqliteCloseNoop:
    """Regression: with_client calls close() after every tool call.

    GrampsSqliteClient.close() must be a no-op so the singleton connection
    stays alive across multiple tool calls within the same session.
    """

    @pytest.mark.asyncio
    async def test_close_does_not_destroy_connection(self, sqlite_client):
        """close() must leave the connection usable for the next query."""
        from gramps_mcp.models.api_calls import ApiCalls
        await sqlite_client.close()
        # The connection must still work after close()
        result = await sqlite_client.make_api_call(ApiCalls.GET_PEOPLE)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_multiple_queries_after_multiple_closes(self, sqlite_client):
        """Simulates with_client calling close() after each tool call."""
        from gramps_mcp.models.api_calls import ApiCalls
        for _ in range(3):
            await sqlite_client.close()
            result = await sqlite_client.make_api_call(ApiCalls.GET_PEOPLE)
            assert isinstance(result, list), "Connection must survive repeated close() calls"
