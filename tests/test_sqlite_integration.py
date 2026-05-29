"""
Integration tests for GrampsSqliteClient against a real Gramps database.

These tests run against your actual Gramps SQLite database to verify that:
  1. _load_sqlite() correctly opens and parses a real database
  2. _normalize() produces the dict shape our handlers expect
  3. Type mappings are correct (EventType values, FamilyRelType, etc.)
  4. All structural invariants hold across every object in the database

Database priority:
  1. GRAMPS_TEST_DB_PATH env var (explicit override)
  2. tests/fixtures/test_gramps.sqlite (anonymized, committed to repo)
  3. Default real DB path (developer machine only)

Run with:
    uv run pytest tests/test_sqlite_integration.py -v -m integration

Run against real DB:
    GRAMPS_TEST_DB_PATH=C:/path/to/sqlite.db uv run pytest -m integration
"""

import os
import shutil
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Database path resolution
# ---------------------------------------------------------------------------

_ANON_DB = Path(__file__).parent / "fixtures" / "test_gramps.sqlite"
_REAL_DB = (
    r"C:\Users\dachner\AppData\Roaming\gramps\grampsdb\6a1764f8\sqlite.db"
)


def _find_db() -> str:
    explicit = os.environ.get("GRAMPS_TEST_DB_PATH")
    if explicit:
        return explicit
    if _ANON_DB.exists():
        return str(_ANON_DB)
    return _REAL_DB


REAL_DB = _find_db()

pytestmark = pytest.mark.integration


def _db_available() -> bool:
    return os.path.exists(REAL_DB)


skip_if_no_db = pytest.mark.skipif(
    not _db_available(),
    reason=f"No Gramps DB found at {REAL_DB}. "
           "Set GRAMPS_TEST_DB_PATH or regenerate tests/fixtures/test_gramps.sqlite.",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def real_client():
    """GrampsSqliteClient connected to the real Gramps database."""
    if not _db_available():
        pytest.skip(f"Real DB not found: {REAL_DB}")
    from gramps_mcp.sqlite_client import GrampsSqliteClient
    return GrampsSqliteClient(REAL_DB)


@pytest.fixture(scope="module")
def real_db(real_client):
    return real_client._db


# ---------------------------------------------------------------------------
# Loader / init
# ---------------------------------------------------------------------------

class TestLoader:
    @skip_if_no_db
    def test_loads_without_error(self, real_db):
        assert real_db is not None

    @skip_if_no_db
    def test_has_people(self, real_db):
        assert real_db.count("person") > 0

    @skip_if_no_db
    def test_has_families(self, real_db):
        assert real_db.count("family") > 0

    @skip_if_no_db
    def test_has_events(self, real_db):
        assert real_db.count("event") > 0

    @skip_if_no_db
    def test_counts_logged(self, real_db, capsys):
        # Just verify counts are reasonable
        people = real_db.count("person")
        events = real_db.count("event")
        print(f"\nDB stats: {people} people, {events} events, "
              f"{real_db.count('family')} families, "
              f"{real_db.count('place')} places, "
              f"{real_db.count('source')} sources")
        assert people > 0


# ---------------------------------------------------------------------------
# Structural invariants: Person
# ---------------------------------------------------------------------------

class TestPersonInvariants:
    @skip_if_no_db
    def test_all_persons_have_handle(self, real_db):
        for p in real_db.all("person"):
            assert "handle" in p, f"Missing handle: {p}"
            assert isinstance(p["handle"], str) and p["handle"]

    @skip_if_no_db
    def test_all_persons_have_gramps_id(self, real_db):
        for p in real_db.all("person"):
            assert "gramps_id" in p, f"Missing gramps_id: {p.get('handle')}"

    @skip_if_no_db
    def test_all_persons_have_primary_name(self, real_db):
        for p in real_db.all("person"):
            pn = p.get("primary_name")
            assert isinstance(pn, dict), (
                f"primary_name is not a dict for {p.get('gramps_id')}: {type(pn)}"
            )

    @skip_if_no_db
    def test_first_name_is_string(self, real_db):
        for p in real_db.all("person"):
            first = p.get("primary_name", {}).get("first_name")
            assert isinstance(first, str), (
                f"first_name not str for {p.get('gramps_id')}: {type(first)}"
            )

    @skip_if_no_db
    def test_surname_list_is_list(self, real_db):
        for p in real_db.all("person"):
            sl = p.get("primary_name", {}).get("surname_list")
            assert isinstance(sl, list), (
                f"surname_list not list for {p.get('gramps_id')}: {type(sl)}"
            )

    @skip_if_no_db
    def test_surname_list_entries_have_surname_key(self, real_db):
        for p in real_db.all("person"):
            for sn in p.get("primary_name", {}).get("surname_list", []):
                assert "surname" in sn, (
                    f"surname key missing in {p.get('gramps_id')}: {sn}"
                )
                assert isinstance(sn["surname"], str)

    @skip_if_no_db
    def test_gender_is_int(self, real_db):
        for p in real_db.all("person"):
            g = p.get("gender")
            assert isinstance(g, int) and g in (0, 1, 2, 3), (
                f"gender invalid for {p.get('gramps_id')}: {g}"
            )

    @skip_if_no_db
    def test_event_ref_list_is_list(self, real_db):
        for p in real_db.all("person"):
            erl = p.get("event_ref_list")
            assert isinstance(erl, list), (
                f"event_ref_list not list for {p.get('gramps_id')}: {type(erl)}"
            )

    @skip_if_no_db
    def test_event_ref_role_is_string(self, real_db):
        for p in real_db.all("person"):
            for eref in p.get("event_ref_list", []):
                role = eref.get("role")
                assert isinstance(role, str), (
                    f"event_ref role not str for {p.get('gramps_id')}: "
                    f"{type(role)} = {role!r}"
                )

    @skip_if_no_db
    def test_no_class_keys_in_person(self, real_db):
        for p in real_db.all("person"):
            assert "_class" not in p, (
                f"_class key leaked into person {p.get('gramps_id')}"
            )
            assert "_class" not in p.get("primary_name", {}), (
                f"_class in primary_name of {p.get('gramps_id')}"
            )

    @skip_if_no_db
    def test_family_list_contains_strings(self, real_db):
        for p in real_db.all("person"):
            for h in p.get("family_list", []):
                assert isinstance(h, str), (
                    f"family_list entry not str for {p.get('gramps_id')}: {type(h)}"
                )


# ---------------------------------------------------------------------------
# Structural invariants: Event
# ---------------------------------------------------------------------------

class TestEventInvariants:
    @skip_if_no_db
    def test_event_type_is_string(self, real_db):
        for ev in real_db.all("event"):
            t = ev.get("type")
            assert isinstance(t, str), (
                f"event type not str for {ev.get('gramps_id')}: "
                f"{type(t)} = {t!r}"
            )

    @skip_if_no_db
    def test_event_type_not_empty(self, real_db):
        unknown_count = sum(
            1 for ev in real_db.all("event")
            if ev.get("type", "").startswith("Unknown(")
        )
        total = real_db.count("event")
        pct = unknown_count / total * 100 if total else 0
        print(f"\n{unknown_count}/{total} events have unmapped type ({pct:.1f}%)")
        # Allow up to 5% unmapped — flags real mapping gaps
        assert pct < 5, f"Too many unmapped event types: {unknown_count}/{total}"

    @skip_if_no_db
    def test_event_date_has_string_key(self, real_db):
        for ev in real_db.all("event"):
            date = ev.get("date", {})
            if date:
                assert "string" in date, (
                    f"date missing 'string' key for event {ev.get('gramps_id')}: "
                    f"{list(date.keys())}"
                )
                assert "text" not in date, (
                    f"date has 'text' key (not normalised) for {ev.get('gramps_id')}"
                )

    @skip_if_no_db
    def test_event_date_dateval_is_list(self, real_db):
        for ev in real_db.all("event"):
            date = ev.get("date", {})
            if date:
                dv = date.get("dateval")
                assert isinstance(dv, list), (
                    f"dateval not list for {ev.get('gramps_id')}: {type(dv)}"
                )


# ---------------------------------------------------------------------------
# Structural invariants: Family
# ---------------------------------------------------------------------------

class TestFamilyInvariants:
    @skip_if_no_db
    def test_family_has_relationship_key(self, real_db):
        for fam in real_db.all("family"):
            assert "relationship" in fam, (
                f"family {fam.get('gramps_id')} missing 'relationship'"
            )

    @skip_if_no_db
    def test_family_has_no_type_key(self, real_db):
        for fam in real_db.all("family"):
            assert "type" not in fam, (
                f"family {fam.get('gramps_id')} has raw 'type' key "
                "(normalization failed)"
            )

    @skip_if_no_db
    def test_relationship_is_string(self, real_db):
        for fam in real_db.all("family"):
            r = fam.get("relationship")
            assert isinstance(r, str), (
                f"relationship not str for {fam.get('gramps_id')}: {type(r)}"
            )

    @skip_if_no_db
    def test_child_ref_frel_is_string(self, real_db):
        for fam in real_db.all("family"):
            for cref in fam.get("child_ref_list", []):
                frel = cref.get("frel")
                assert isinstance(frel, str), (
                    f"child_ref frel not str in {fam.get('gramps_id')}: "
                    f"{type(frel)} = {frel!r}"
                )


# ---------------------------------------------------------------------------
# Structural invariants: Place
# ---------------------------------------------------------------------------

class TestPlaceInvariants:
    @skip_if_no_db
    def test_place_type_is_string(self, real_db):
        for pl in real_db.all("place"):
            pt = pl.get("place_type")
            assert isinstance(pt, str), (
                f"place_type not str for {pl.get('gramps_id')}: {type(pt)}"
            )


# ---------------------------------------------------------------------------
# Cross-reference consistency
# ---------------------------------------------------------------------------

class TestCrossReferences:
    @skip_if_no_db
    def test_event_refs_resolve(self, real_db):
        """Every eventref in a person must point to an existing event."""
        missing = []
        for p in real_db.all("person"):
            for eref in p.get("event_ref_list", []):
                h = eref.get("ref", "")
                if h and real_db.get("event", h) is None:
                    missing.append((p.get("gramps_id"), h))
        assert not missing, f"Dangling event refs: {missing[:5]}"

    @skip_if_no_db
    def test_family_refs_resolve(self, real_db):
        """Every family_list handle in a person must exist."""
        missing = []
        for p in real_db.all("person"):
            for fh in p.get("family_list", []):
                if real_db.get("family", fh) is None:
                    missing.append((p.get("gramps_id"), fh))
        assert not missing, f"Dangling family refs: {missing[:5]}"

    @skip_if_no_db
    def test_birth_ref_index_in_range(self, real_db):
        """birth_ref_index must be -1 or a valid index into event_ref_list."""
        bad = []
        for p in real_db.all("person"):
            bi = p.get("birth_ref_index", -1)
            erl = p.get("event_ref_list", [])
            if bi != -1 and not (0 <= bi < len(erl)):
                bad.append((p.get("gramps_id"), bi, len(erl)))
        assert not bad, f"birth_ref_index out of range: {bad[:5]}"


# ---------------------------------------------------------------------------
# Handler smoke tests (do our dicts pass through the handlers without crash?)
# ---------------------------------------------------------------------------

class TestHandlerSmoke:
    @skip_if_no_db
    @pytest.mark.asyncio
    async def test_format_person_runs(self, real_client, real_db):
        """format_person handler must not crash on the first person."""
        from gramps_mcp.handlers.person_handler import format_person
        person = next(iter(real_db.all("person")))
        result = await format_person(real_client, "default", person["handle"])
        assert isinstance(result, str)
        assert len(result) > 0

    @skip_if_no_db
    @pytest.mark.asyncio
    async def test_format_family_runs(self, real_client, real_db):
        """format_family handler must not crash on the first family."""
        from gramps_mcp.handlers.family_handler import format_family
        family = next(iter(real_db.all("family")))
        result = await format_family(real_client, "default", family["handle"])
        assert isinstance(result, str)
        assert len(result) > 0

    @skip_if_no_db
    @pytest.mark.asyncio
    async def test_format_note_handler(self, real_client, real_db):
        """format_note handler must not crash."""
        if real_db.count("note") == 0:
            pytest.skip("No notes in DB")
        from gramps_mcp.handlers.note_handler import format_note
        note = next(iter(real_db.all("note")))
        result = await format_note(real_client, "default", note["handle"])
        assert isinstance(result, str)

    @skip_if_no_db
    @pytest.mark.asyncio
    async def test_format_place_inline(self, real_client, real_db):
        """format_place handler must not crash."""
        if real_db.count("place") == 0:
            pytest.skip("No places in DB")
        from gramps_mcp.handlers.place_handler import format_place
        place = next(iter(real_db.all("place")))
        result = await format_place(real_client, "default", place["handle"], inline=True)
        assert isinstance(result, str)

    @skip_if_no_db
    @pytest.mark.asyncio
    async def test_format_source_runs(self, real_client, real_db):
        """format_source handler must not crash."""
        if real_db.count("source") == 0:
            pytest.skip("No sources in DB")
        from gramps_mcp.handlers.source_handler import format_source
        source = next(iter(real_db.all("source")))
        result = await format_source(real_client, "default", source["handle"])
        assert isinstance(result, str)

    @skip_if_no_db
    @pytest.mark.asyncio
    async def test_format_citation_runs(self, real_client, real_db):
        """format_citation handler must not crash."""
        if real_db.count("citation") == 0:
            pytest.skip("No citations in DB")
        from gramps_mcp.handlers.citation_handler import format_citation
        citation = next(iter(real_db.all("citation")))
        result = await format_citation(real_client, "default", citation["handle"])
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Structural invariants: Source / Citation / Repository / Media / Note
# ---------------------------------------------------------------------------


class TestSourceInvariants:
    @skip_if_no_db
    def test_source_title_is_string(self, real_db):
        for src in real_db.all("source"):
            t = src.get("title")
            assert isinstance(t, str), (
                f"source title not str for {src.get('gramps_id')}: {type(t)}"
            )

    @skip_if_no_db
    def test_source_note_list_is_list(self, real_db):
        for src in real_db.all("source"):
            nl = src.get("note_list")
            assert isinstance(nl, list), (
                f"source note_list not list for {src.get('gramps_id')}: {type(nl)}"
            )

    @skip_if_no_db
    def test_source_reporef_list_is_list(self, real_db):
        for src in real_db.all("source"):
            rl = src.get("reporef_list")
            assert isinstance(rl, list), (
                f"source reporef_list not list for {src.get('gramps_id')}: {type(rl)}"
            )

    @skip_if_no_db
    def test_source_reporef_has_ref_key(self, real_db):
        for src in real_db.all("source"):
            for rref in src.get("reporef_list", []):
                assert "ref" in rref, (
                    f"reporef missing 'ref' in source {src.get('gramps_id')}: {rref}"
                )
                assert isinstance(rref["ref"], str)

    @skip_if_no_db
    def test_source_media_list_is_list(self, real_db):
        for src in real_db.all("source"):
            ml = src.get("media_list")
            assert isinstance(ml, list), (
                f"source media_list not list for {src.get('gramps_id')}: {type(ml)}"
            )

    @skip_if_no_db
    def test_source_no_class_keys(self, real_db):
        for src in real_db.all("source"):
            assert "_class" not in src, (
                f"_class leaked into source {src.get('gramps_id')}"
            )


class TestCitationInvariants:
    @skip_if_no_db
    def test_citation_page_is_string(self, real_db):
        for cit in real_db.all("citation"):
            p = cit.get("page")
            assert isinstance(p, str), (
                f"citation page not str for {cit.get('gramps_id')}: {type(p)}"
            )

    @skip_if_no_db
    def test_citation_confidence_is_int(self, real_db):
        for cit in real_db.all("citation"):
            c = cit.get("confidence")
            assert isinstance(c, int), (
                f"citation confidence not int for {cit.get('gramps_id')}: {type(c)}"
            )

    @skip_if_no_db
    def test_citation_source_handle_resolves(self, real_db):
        missing = []
        for cit in real_db.all("citation"):
            sh = cit.get("source_handle")
            if sh and real_db.get("source", sh) is None:
                missing.append((cit.get("gramps_id"), sh))
        assert not missing, f"Dangling source refs in citations: {missing[:5]}"

    @skip_if_no_db
    def test_citation_date_normalised(self, real_db):
        for cit in real_db.all("citation"):
            date = cit.get("date", {})
            if date:
                assert "string" in date, (
                    f"citation date missing 'string' for {cit.get('gramps_id')}"
                )
                assert "text" not in date, (
                    f"citation date has raw 'text' for {cit.get('gramps_id')}"
                )


class TestRepositoryInvariants:
    @skip_if_no_db
    def test_repository_name_is_string(self, real_db):
        for repo in real_db.all("repository"):
            n = repo.get("name")
            assert isinstance(n, str), (
                f"repo name not str for {repo.get('gramps_id')}: {type(n)}"
            )

    @skip_if_no_db
    def test_repository_urls_is_list(self, real_db):
        for repo in real_db.all("repository"):
            urls = repo.get("urls")
            assert isinstance(urls, list), (
                f"repo urls not list for {repo.get('gramps_id')}: {type(urls)}"
            )

    @skip_if_no_db
    def test_repository_no_class_keys(self, real_db):
        for repo in real_db.all("repository"):
            assert "_class" not in repo, (
                f"_class leaked into repository {repo.get('gramps_id')}"
            )


class TestMediaInvariants:
    @skip_if_no_db
    def test_media_path_is_string(self, real_db):
        for m in real_db.all("media"):
            p = m.get("path")
            assert isinstance(p, str), (
                f"media path not str for {m.get('gramps_id')}: {type(p)}"
            )

    @skip_if_no_db
    def test_media_mime_is_string(self, real_db):
        for m in real_db.all("media"):
            mime = m.get("mime")
            assert isinstance(mime, str), (
                f"media mime not str for {m.get('gramps_id')}: {type(mime)}"
            )

    @skip_if_no_db
    def test_media_date_normalised(self, real_db):
        for m in real_db.all("media"):
            date = m.get("date", {})
            if date:
                assert "string" in date, (
                    f"media date missing 'string' for {m.get('gramps_id')}"
                )


class TestNoteInvariants:
    @skip_if_no_db
    def test_note_text_has_string_key(self, real_db):
        for note in real_db.all("note"):
            text = note.get("text")
            if isinstance(text, dict):
                assert "string" in text, (
                    f"note text dict missing 'string' for {note.get('gramps_id')}: "
                    f"{list(text.keys())}"
                )

    @skip_if_no_db
    def test_note_no_class_keys(self, real_db):
        for note in real_db.all("note"):
            assert "_class" not in note, (
                f"_class leaked into note {note.get('gramps_id')}"
            )


# ---------------------------------------------------------------------------
# Date variety — daterange, datespan, datestr
# ---------------------------------------------------------------------------


class TestDateVariety:
    @skip_if_no_db
    def test_daterange_normalised(self, real_db):
        """Events with daterange must have modifier=4 and a 'string' key."""
        checked = 0
        for ev in real_db.all("event"):
            date = ev.get("date", {})
            if date.get("modifier") == 4:  # between
                assert "string" in date, (
                    f"daterange missing 'string' for {ev.get('gramps_id')}"
                )
                assert "text" not in date
                checked += 1
        print(f"\n  daterange events found: {checked}")

    @skip_if_no_db
    def test_datespan_normalised(self, real_db):
        """Events with datespan must have modifier=5."""
        checked = 0
        for ev in real_db.all("event"):
            date = ev.get("date", {})
            if date.get("modifier") == 5:  # from…to
                assert "string" in date
                assert "text" not in date
                checked += 1
        print(f"\n  datespan events found: {checked}")

    @skip_if_no_db
    def test_datestr_normalised(self, real_db):
        """Text-only dates (modifier=6) must have a non-empty 'string'."""
        checked = 0
        for ev in real_db.all("event"):
            date = ev.get("date", {})
            if date.get("modifier") == 6:  # text only
                assert "string" in date
                assert "text" not in date
                # datestr should have a meaningful string value
                assert isinstance(date["string"], str)
                checked += 1
        print(f"\n  datestr events found: {checked}")

    @skip_if_no_db
    def test_no_raw_text_key_anywhere(self, real_db):
        """No date dict in any object should have a 'text' key after normalisation."""
        violations = []
        for obj_type in ("person", "family", "event", "citation", "media"):
            for obj in real_db.all(obj_type):
                date = obj.get("date", {})
                if isinstance(date, dict) and "text" in date:
                    violations.append((obj_type, obj.get("gramps_id")))
        assert not violations, (
            f"Raw 'text' key found in date dicts: {violations[:5]}"
        )


# ---------------------------------------------------------------------------
# Write roundtrip — write to disk, reopen, verify
# ---------------------------------------------------------------------------


class TestWriteRoundtrip:
    @skip_if_no_db
    def test_create_person_persists_to_disk(self, tmp_path):
        """Write a new person → close connection → reopen → person still there."""
        from gramps_mcp.sqlite_client import GrampsSqliteClient

        # Fresh copy so we don't modify the shared fixture
        db_copy = tmp_path / "roundtrip.sqlite"
        shutil.copy(REAL_DB, db_copy)

        client = GrampsSqliteClient(str(db_copy))
        new_person = {
            "gender": 0,
            "primary_name": {
                "first_name": "Roundtrip",
                "surname_list": [
                    {"surname": "Test", "primary": True, "prefix": "", "connector": ""}
                ],
                "suffix": "", "title": "", "call": "", "nick": "",
                "type": "Birth Name",
            },
            "event_ref_list": [], "family_list": [], "parent_family_list": [],
            "note_list": [], "citation_list": [], "media_list": [],
            "address_list": [], "urls": [],
        }
        created = client._db.put("person", new_person)
        handle = created["handle"]
        gramps_id = created["gramps_id"]
        client._db.close()

        # Reopen and verify
        client2 = GrampsSqliteClient(str(db_copy))
        fetched = client2._db.get("person", handle)
        assert fetched is not None, "Person not found after reopen"
        assert fetched["gramps_id"] == gramps_id
        assert fetched["primary_name"]["first_name"] == "Roundtrip"
        assert fetched["primary_name"]["surname_list"][0]["surname"] == "Test"
        assert fetched["gender"] == 0
        client2._db.close()

    @skip_if_no_db
    def test_update_person_persists_to_disk(self, tmp_path):
        """Update an existing person → close → reopen → change visible."""
        from gramps_mcp.sqlite_client import GrampsSqliteClient

        db_copy = tmp_path / "update_roundtrip.sqlite"
        shutil.copy(REAL_DB, db_copy)

        client = GrampsSqliteClient(str(db_copy))
        # Get any person
        person = next(iter(client._db.all("person")))
        handle = person["handle"]
        original_gender = person["gender"]
        new_gender = 0 if original_gender == 1 else 1

        client._db.put("person", {**person, "gender": new_gender})
        client._db.close()

        client2 = GrampsSqliteClient(str(db_copy))
        fetched = client2._db.get("person", handle)
        assert fetched["gender"] == new_gender, (
            f"Gender not updated: expected {new_gender}, got {fetched['gender']}"
        )
        client2._db.close()

    @skip_if_no_db
    def test_create_event_with_type_persists(self, tmp_path):
        """Event type must survive denorm → SQLite → renorm roundtrip."""
        from gramps_mcp.sqlite_client import GrampsSqliteClient

        db_copy = tmp_path / "event_roundtrip.sqlite"
        shutil.copy(REAL_DB, db_copy)

        client = GrampsSqliteClient(str(db_copy))
        new_event = {
            "type": "Baptism",
            "date": {"dateval": [12, 6, 1880, False], "modifier": 0,
                     "quality": 0, "string": ""},
            "description": "Taufe in St. Marien",
            "place": None,
            "note_list": [], "citation_list": [],
        }
        created = client._db.put("event", new_event)
        handle = created["handle"]
        client._db.close()

        client2 = GrampsSqliteClient(str(db_copy))
        fetched = client2._db.get("event", handle)
        assert fetched["type"] == "Baptism", (
            f"Event type not preserved: {fetched['type']!r}"
        )
        assert fetched["date"]["dateval"] == [12, 6, 1880, False]
        assert fetched["description"] == "Taufe in St. Marien"
        client2._db.close()
