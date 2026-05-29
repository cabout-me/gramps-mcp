"""
Unit tests for GrampsDirectClient (XML-based direct backend).

All tests use the synthetic fixture defined in conftest.py — no Gramps Python
package, no GTK, no external server required.

Run with:
    uv run pytest tests/test_direct_client.py -v
"""

import pytest

from gramps_mcp.client import GrampsAPIError
from gramps_mcp.models.api_calls import ApiCalls


# ===========================================================================
# XML parsing: Person
# ===========================================================================


class TestPersonParsing:
    def test_count(self, db):
        assert len(db.all("person")) == 6

    def test_basic_fields(self, db):
        john = db.get("person", "h_pe_john")
        assert john["gramps_id"] == "I0001"
        assert john["handle"] == "h_pe_john"

    def test_gender_male(self, db):
        assert db.get("person", "h_pe_john")["gender"] == 1

    def test_gender_female(self, db):
        assert db.get("person", "h_pe_jane")["gender"] == 0

    def test_gender_unknown(self, db):
        assert db.get("person", "h_pe_unknown")["gender"] == 2

    def test_name_first_and_surname(self, db):
        name = db.get("person", "h_pe_john")["primary_name"]
        assert name["first_name"] == "John Robert"
        assert name["surname_list"][0]["surname"] == "Smith"

    def test_name_suffix(self, db):
        name = db.get("person", "h_pe_john")["primary_name"]
        assert name["suffix"] == "Jr."

    def test_name_call_and_nick(self, db):
        name = db.get("person", "h_pe_john")["primary_name"]
        assert name["call"] == "Rob"
        assert name["nick"] == "Bobby"

    def test_name_title(self, db):
        name = db.get("person", "h_pe_john")["primary_name"]
        assert name["title"] == "Dr."

    def test_name_type(self, db):
        name = db.get("person", "h_pe_john")["primary_name"]
        assert name["type"] == "Birth Name"

    def test_birth_ref_index(self, db):
        john = db.get("person", "h_pe_john")
        assert john["birth_ref_index"] == 0
        assert john["event_ref_list"][0]["ref"] == "h_ev_birth_john"

    def test_death_ref_index(self, db):
        assert db.get("person", "h_pe_john")["death_ref_index"] == 1

    def test_no_death_event(self, db):
        assert db.get("person", "h_pe_jane")["death_ref_index"] == -1

    def test_family_list(self, db):
        john = db.get("person", "h_pe_john")
        assert "h_fa_smith" in john["family_list"]
        assert john["parent_family_list"] == []

    def test_parent_family_list(self, db):
        child = db.get("person", "h_pe_child")
        assert "h_fa_smith" in child["parent_family_list"]
        assert child["family_list"] == []

    def test_note_list(self, db):
        assert "h_no_john" in db.get("person", "h_pe_john")["note_list"]

    def test_citation_list(self, db):
        assert "h_ci_birth" in db.get("person", "h_pe_john")["citation_list"]

    def test_media_list(self, db):
        media = db.get("person", "h_pe_john")["media_list"]
        assert len(media) == 1
        assert media[0]["ref"] == "h_me_photo"

    def test_urls(self, db):
        urls = db.get("person", "h_pe_john")["urls"]
        assert len(urls) == 1
        assert urls[0]["path"] == "https://example.com/john"
        assert urls[0]["description"] == "Homepage"

    def test_event_ref_role(self, db):
        john = db.get("person", "h_pe_john")
        assert john["event_ref_list"][0]["role"] == "Primary"

    def test_get_by_gramps_id(self, db):
        person = db.get_by_id("person", "I0001")
        assert person is not None
        assert person["handle"] == "h_pe_john"

    def test_missing_handle_returns_none(self, db):
        assert db.get("person", "nonexistent") is None


# ===========================================================================
# XML parsing: Event
# ===========================================================================


class TestEventParsing:
    def test_count(self, db):
        assert len(db.all("event")) == 9

    def test_basic_fields(self, db):
        ev = db.get("event", "h_ev_birth_john")
        assert ev["gramps_id"] == "E0001"
        assert ev["type"] == "Birth"

    def test_dateval_simple(self, db):
        date = db.get("event", "h_ev_birth_john")["date"]
        assert date["dateval"] == [15, 6, 1950, False]
        assert date["modifier"] == 0
        assert date["quality"] == 0
        assert date["string"] == ""

    def test_dateval_about_estimated(self, db):
        date = db.get("event", "h_ev_death_john")["date"]
        assert date["modifier"] == 3   # about
        assert date["quality"] == 1    # estimated

    def test_daterange(self, db):
        date = db.get("event", "h_ev_birth_child")["date"]
        assert date["modifier"] == 4   # between
        assert date["quality"] == 1    # estimated
        assert "between" in date["string"]
        assert "1976" in date["string"]

    def test_datespan(self, db):
        date = db.get("event", "h_ev_residence")["date"]
        assert date["modifier"] == 5   # from...to
        assert "from" in date["string"]
        assert "1980" in date["string"]

    def test_datestr(self, db):
        date = db.get("event", "h_ev_textdate")["date"]
        assert date["modifier"] == 6   # text only
        assert date["string"] == "Michaelmas 1901"
        assert date["dateval"] == []

    def test_place_handle(self, db):
        assert db.get("event", "h_ev_birth_john")["place"] == "h_pl_berlin"

    def test_no_place(self, db):
        assert db.get("event", "h_ev_birth_jane")["place"] == ""

    def test_description(self, db):
        ev = db.get("event", "h_ev_residence")
        assert ev["description"] == "Lived in Hamburg"

    def test_no_description(self, db):
        assert db.get("event", "h_ev_birth_john")["description"] == ""


# ===========================================================================
# XML parsing: Family
# ===========================================================================


class TestFamilyParsing:
    def test_count(self, db):
        assert len(db.all("family")) == 2

    def test_basic_fields(self, db):
        fam = db.get("family", "h_fa_smith")
        assert fam["gramps_id"] == "F0001"
        assert fam["relationship"] == "Married"

    def test_parents(self, db):
        fam = db.get("family", "h_fa_smith")
        assert fam["father_handle"] == "h_pe_john"
        assert fam["mother_handle"] == "h_pe_jane"

    def test_children(self, db):
        refs = db.get("family", "h_fa_smith")["child_ref_list"]
        assert len(refs) == 1
        assert refs[0]["ref"] == "h_pe_child"
        assert refs[0]["frel"] == "Birth"
        assert refs[0]["mrel"] == "Birth"

    def test_event_refs(self, db):
        refs = db.get("family", "h_fa_smith")["event_ref_list"]
        assert len(refs) == 1
        assert refs[0]["ref"] == "h_ev_marriage"
        assert refs[0]["role"] == "Family"

    def test_note_list(self, db):
        assert "h_no_john" in db.get("family", "h_fa_smith")["note_list"]


# ===========================================================================
# XML parsing: Place
# ===========================================================================


class TestPlaceParsing:
    def test_count(self, db):
        assert len(db.all("place")) == 3

    def test_title(self, db):
        place = db.get("place", "h_pl_berlin")
        assert place["title"] == "Berlin, Germany"

    def test_name_value(self, db):
        place = db.get("place", "h_pl_berlin")
        assert place["name"]["value"] == "Berlin"

    def test_place_type(self, db):
        assert db.get("place", "h_pl_berlin")["place_type"] == "City"

    def test_placeref(self, db):
        refs = db.get("place", "h_pl_hamburg")["placeref_list"]
        assert len(refs) == 1
        assert refs[0]["ref"] == "h_pl_germany"

    def test_no_placeref(self, db):
        assert db.get("place", "h_pl_berlin")["placeref_list"] == []

    def test_url(self, db):
        urls = db.get("place", "h_pl_berlin")["urls"]
        assert len(urls) == 1
        assert "wikipedia" in urls[0]["path"]


# ===========================================================================
# XML parsing: Source
# ===========================================================================


class TestSourceParsing:
    def test_count(self, db):
        assert len(db.all("source")) == 1

    def test_fields(self, db):
        src = db.get("source", "h_so_civil")
        assert src["gramps_id"] == "S0001"
        assert src["title"] == "Civil Records Office"
        assert src["author"] == "State Archive"
        assert src["pubinfo"] == "Berlin, 1950"
        assert src["abbrev"] == "CRO"

    def test_reporef_list_present(self, db):
        src = db.get("source", "h_so_civil")
        assert "reporef_list" in src
        assert len(src["reporef_list"]) == 1

    def test_reporef_list_ref(self, db):
        ref = db.get("source", "h_so_civil")["reporef_list"][0]
        assert ref["ref"] == "h_re_archive"

    def test_reporef_callno_and_medium(self, db):
        ref = db.get("source", "h_so_civil")["reporef_list"][0]
        assert ref["callno"] == "Vol. 3"
        assert ref["medium"] == "Book"

    def test_source_media_list(self, db):
        src = db.get("source", "h_so_civil")
        assert len(src["media_list"]) == 1
        assert src["media_list"][0]["ref"] == "h_me_photo"


# ===========================================================================
# XML parsing: Citation
# ===========================================================================


class TestCitationParsing:
    def test_count(self, db):
        assert len(db.all("citation")) == 1

    def test_fields(self, db):
        cit = db.get("citation", "h_ci_birth")
        assert cit["gramps_id"] == "C0001"
        assert cit["page"] == "Certificate No. 12345"
        assert cit["confidence"] == 2
        assert cit["source_handle"] == "h_so_civil"

    def test_date(self, db):
        date = db.get("citation", "h_ci_birth")["date"]
        assert date["dateval"] == [15, 1, 2024, False]

    def test_note_list(self, db):
        assert "h_no_john" in db.get("citation", "h_ci_birth")["note_list"]


# ===========================================================================
# XML parsing: Note
# ===========================================================================


class TestNoteParsing:
    def test_count(self, db):
        assert len(db.all("note")) == 1

    def test_fields(self, db):
        note = db.get("note", "h_no_john")
        assert note["gramps_id"] == "N0001"
        assert note["type"] == "General"
        assert "John Smith" in note["text"]["string"]


# ===========================================================================
# XML parsing: Media
# ===========================================================================


class TestMediaParsing:
    def test_count(self, db):
        assert len(db.all("media")) == 1

    def test_fields(self, db):
        media = db.get("media", "h_me_photo")
        assert media["gramps_id"] == "O0001"
        assert media["path"] == "/photos/family.jpg"
        assert media["mime"] == "image/jpeg"
        assert media["desc"] == "Family photo 1975"
        assert media["checksum"] == "abc123def456"


# ===========================================================================
# XML parsing: Repository
# ===========================================================================


class TestRepositoryParsing:
    def test_count(self, db):
        assert len(db.all("repository")) == 1

    def test_fields(self, db):
        repo = db.get("repository", "h_re_archive")
        assert repo["gramps_id"] == "R0001"
        assert repo["name"] == "State Archive Berlin"
        assert repo["type"] == "Archive"

    def test_urls(self, db):
        urls = db.get("repository", "h_re_archive")["urls"]
        assert len(urls) == 1
        assert urls[0]["path"] == "https://archive.berlin.de"


# ===========================================================================
# Extended blocks
# ===========================================================================


class TestExtendedBlocks:
    def test_person_extended_events(self, db):
        john = db.get("person", "h_pe_john")
        ext = db.build_extended_person(john)
        assert len(ext["events"]) == 2
        types = {e["type"] for e in ext["events"]}
        assert types == {"Birth", "Death"}

    def test_person_extended_families(self, db):
        john = db.get("person", "h_pe_john")
        ext = db.build_extended_person(john)
        assert len(ext["families"]) == 1
        assert ext["families"][0]["gramps_id"] == "F0001"

    def test_person_extended_parent_families(self, db):
        john = db.get("person", "h_pe_john")
        ext = db.build_extended_person(john)
        assert ext["parent_families"] == []

    def test_child_extended_parent_families(self, db):
        child = db.get("person", "h_pe_child")
        ext = db.build_extended_person(child)
        assert len(ext["parent_families"]) == 1
        assert ext["parent_families"][0]["gramps_id"] == "F0001"

    def test_family_extended_events(self, db):
        fam = db.get("family", "h_fa_smith")
        ext = db.build_extended_family(fam)
        assert len(ext["events"]) == 1
        assert ext["events"][0]["type"] == "Marriage"

    def test_family_extended_parents(self, db):
        fam = db.get("family", "h_fa_smith")
        ext = db.build_extended_family(fam)
        assert ext["father"]["gramps_id"] == "I0001"
        assert ext["mother"]["gramps_id"] == "I0002"

    def test_family_extended_children(self, db):
        fam = db.get("family", "h_fa_smith")
        ext = db.build_extended_family(fam)
        assert len(ext["children"]) == 1
        assert ext["children"][0]["gramps_id"] == "I0003"


# ===========================================================================
# GrampsDirectClient API
# ===========================================================================


class TestApiGetSingle:
    @pytest.mark.asyncio
    async def test_get_person(self, client):
        person = await client.make_api_call(ApiCalls.GET_PERSON, handle="h_pe_john")
        assert person["gramps_id"] == "I0001"

    @pytest.mark.asyncio
    async def test_get_person_with_extended(self, client):
        person = await client.make_api_call(
            ApiCalls.GET_PERSON, params={"extend": "all"}, handle="h_pe_john"
        )
        ext = person["extended"]
        assert len(ext["events"]) == 2
        assert len(ext["families"]) == 1

    @pytest.mark.asyncio
    async def test_get_family_with_extended(self, client):
        fam = await client.make_api_call(
            ApiCalls.GET_FAMILY, params={"extend": "all"}, handle="h_fa_smith"
        )
        ext = fam["extended"]
        assert ext["father"]["gramps_id"] == "I0001"
        assert ext["mother"]["gramps_id"] == "I0002"
        assert len(ext["children"]) == 1

    @pytest.mark.asyncio
    async def test_get_missing_handle_raises(self, client):
        with pytest.raises(GrampsAPIError, match="not found"):
            await client.make_api_call(ApiCalls.GET_PERSON, handle="nonexistent")

    @pytest.mark.asyncio
    async def test_get_missing_handle_arg_raises(self, client):
        with pytest.raises(GrampsAPIError, match="handle is required"):
            await client.make_api_call(ApiCalls.GET_PERSON, handle="")


class TestApiGetList:
    @pytest.mark.asyncio
    async def test_list_all_people(self, client):
        people = await client.make_api_call(
            ApiCalls.GET_PEOPLE, params={"pagesize": 100}
        )
        assert len(people) == 6

    @pytest.mark.asyncio
    async def test_filter_by_gramps_id(self, client):
        people = await client.make_api_call(
            ApiCalls.GET_PEOPLE, params={"gramps_id": "I0001"}
        )
        assert len(people) == 1
        assert people[0]["gramps_id"] == "I0001"

    @pytest.mark.asyncio
    async def test_name_filter(self, client):
        people = await client.make_api_call(
            ApiCalls.GET_PEOPLE, params={"query": "smith", "pagesize": 10}
        )
        ids = {p["gramps_id"] for p in people}
        assert "I0001" in ids  # John Smith
        assert "I0003" in ids  # James Smith

    @pytest.mark.asyncio
    async def test_pagination_page1(self, client):
        page = await client.make_api_call(
            ApiCalls.GET_PEOPLE, params={"pagesize": 2, "page": 1}
        )
        assert len(page) == 2

    @pytest.mark.asyncio
    async def test_pagination_page2(self, client):
        page1 = await client.make_api_call(
            ApiCalls.GET_PEOPLE, params={"pagesize": 2, "page": 1}
        )
        page2 = await client.make_api_call(
            ApiCalls.GET_PEOPLE, params={"pagesize": 2, "page": 2}
        )
        assert len(page2) == 2
        handles1 = {p["handle"] for p in page1}
        handles2 = {p["handle"] for p in page2}
        assert handles1.isdisjoint(handles2)

    @pytest.mark.asyncio
    async def test_list_events(self, client):
        events = await client.make_api_call(
            ApiCalls.GET_EVENTS, params={"pagesize": 100}
        )
        assert len(events) == 9

    @pytest.mark.asyncio
    async def test_list_places(self, client):
        places = await client.make_api_call(
            ApiCalls.GET_PLACES, params={"pagesize": 100}
        )
        assert len(places) == 3


class TestApiSearch:
    @pytest.mark.asyncio
    async def test_search_by_surname(self, client):
        results = await client.make_api_call(
            ApiCalls.GET_SEARCH, params={"query": "smith", "pagesize": 20}
        )
        types = {r["object_type"] for r in results}
        assert "person" in types

    @pytest.mark.asyncio
    async def test_search_empty_query(self, client):
        results = await client.make_api_call(
            ApiCalls.GET_SEARCH, params={"query": ""}
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_search_place(self, client):
        results = await client.make_api_call(
            ApiCalls.GET_SEARCH, params={"query": "berlin", "pagesize": 10}
        )
        types = {r["object_type"] for r in results}
        assert "place" in types


class TestApiTreeInfo:
    @pytest.mark.asyncio
    async def test_tree_info(self, client):
        info = await client.make_api_call(ApiCalls.GET_TREE)
        assert info["usage_people"] == 6
        assert info["usage_families"] == 2
        assert info["usage_events"] == 9
        assert info["usage_places"] == 3
        assert info["usage_sources"] == 1
        assert info["usage_citations"] == 1
        assert info["usage_notes"] == 1
        assert info["usage_media"] == 1
        assert info["usage_repositories"] == 1

    @pytest.mark.asyncio
    async def test_tree_info_name(self, client, gpkg_path):
        import os
        info = await client.make_api_call(ApiCalls.GET_TREE)
        expected = os.path.splitext(os.path.basename(gpkg_path))[0]
        assert info["name"] == expected


class TestApiWriteNotSupported:
    @pytest.mark.asyncio
    async def test_post_people_raises(self, client):
        with pytest.raises(GrampsAPIError, match="write access"):
            await client.make_api_call(ApiCalls.POST_PEOPLE, params={})

    @pytest.mark.asyncio
    async def test_put_person_raises(self, client):
        with pytest.raises(GrampsAPIError, match="write access"):
            await client.make_api_call(ApiCalls.PUT_PERSON, params={}, handle="h_pe_john")

    @pytest.mark.asyncio
    async def test_with_headers(self, client):
        result, headers = await client.make_api_call(
            ApiCalls.GET_PEOPLE, params={"pagesize": 100}, with_headers=True
        )
        assert len(result) == 6
        assert headers["x-total-count"] == "6"


# ===========================================================================
# Handler integration
# ===========================================================================


class TestHandlers:
    @pytest.mark.asyncio
    async def test_format_person(self, client):
        from gramps_mcp.handlers.person_handler import format_person

        result = await format_person(client, "default", "h_pe_john")
        assert "John Robert Smith" in result
        assert "I0001" in result
        assert "15 June 1950" in result       # birth date formatted
        assert "Berlin, Germany" in result    # birth place resolved

    @pytest.mark.asyncio
    async def test_format_person_death(self, client):
        from gramps_mcp.handlers.person_handler import format_person

        result = await format_person(client, "default", "h_pe_john")
        assert "Died" in result
        assert "Hamburg" in result

    @pytest.mark.asyncio
    async def test_format_family(self, client):
        from gramps_mcp.handlers.family_handler import format_family

        result = await format_family(client, "default", "h_fa_smith")
        assert "F0001" in result
        assert "John Robert Smith" in result
        assert "Jane Doe" in result
        assert "20 April 1975" in result      # marriage date

    @pytest.mark.asyncio
    async def test_format_family_children(self, client):
        from gramps_mcp.handlers.family_handler import format_family

        result = await format_family(client, "default", "h_fa_smith")
        assert "James Smith" in result        # child name

    @pytest.mark.asyncio
    async def test_format_place_inline(self, client):
        from gramps_mcp.handlers.place_handler import format_place

        result = await format_place(client, "default", "h_pl_berlin", inline=True)
        assert "Berlin" in result

    @pytest.mark.asyncio
    async def test_format_place_with_hierarchy(self, client):
        from gramps_mcp.handlers.place_handler import format_place

        # Hamburg has a parent place (Germany)
        result = await format_place(client, "default", "h_pl_hamburg", inline=True)
        assert "Hamburg" in result


# ===========================================================================
# XML parsing: Address (TDD — Test family, Baumallee 12, Testhausen)
# ===========================================================================


class TestAddressParsing:
    def test_address_list_present(self, db):
        testor = db.get("person", "h_pe_testor")
        assert "address_list" in testor

    def test_address_list_length(self, db):
        assert len(db.get("person", "h_pe_testor")["address_list"]) == 1

    def test_address_street(self, db):
        addr = db.get("person", "h_pe_testor")["address_list"][0]
        assert addr["street"] == "Baumallee 12"

    def test_address_city(self, db):
        addr = db.get("person", "h_pe_testor")["address_list"][0]
        assert addr["city"] == "Testhausen"

    def test_address_empty_fields(self, db):
        addr = db.get("person", "h_pe_testor")["address_list"][0]
        for field in ("locality", "county", "state", "country", "postal", "phone"):
            assert addr[field] == "", f"expected empty {field!r}"

    def test_address_no_date(self, db):
        addr = db.get("person", "h_pe_testor")["address_list"][0]
        assert addr["date"] == {}

    def test_address_no_notes(self, db):
        addr = db.get("person", "h_pe_testor")["address_list"][0]
        assert addr["note_list"] == []

    def test_address_on_testiane(self, db):
        addr = db.get("person", "h_pe_testiane")["address_list"][0]
        assert addr["street"] == "Baumallee 12"
        assert addr["city"] == "Testhausen"

    def test_no_address_on_john(self, db):
        john = db.get("person", "h_pe_john")
        assert john["address_list"] == []


# ===========================================================================
# Sibling relationship: Testor & Testiane share parent family F0002
# ===========================================================================


class TestTestSiblings:
    def test_testor_name(self, db):
        testor = db.get("person", "h_pe_testor")
        pn = testor["primary_name"]
        assert pn["first_name"] == "Testor"
        assert pn["surname_list"][0]["surname"] == "von Test"

    def test_testiane_name(self, db):
        testiane = db.get("person", "h_pe_testiane")
        pn = testiane["primary_name"]
        assert pn["first_name"] == "Testiane"
        assert pn["surname_list"][0]["surname"] == "von Test"

    def test_testor_gender(self, db):
        assert db.get("person", "h_pe_testor")["gender"] == 1  # M

    def test_testiane_gender(self, db):
        assert db.get("person", "h_pe_testiane")["gender"] == 0  # F

    def test_testor_in_test_family(self, db):
        testor = db.get("person", "h_pe_testor")
        assert "h_fa_test" in testor["parent_family_list"]

    def test_testiane_in_test_family(self, db):
        testiane = db.get("person", "h_pe_testiane")
        assert "h_fa_test" in testiane["parent_family_list"]

    def test_test_family_has_two_children(self, db):
        fam = db.get("family", "h_fa_test")
        assert len(fam["child_ref_list"]) == 2

    def test_test_family_children_handles(self, db):
        fam = db.get("family", "h_fa_test")
        child_handles = {c["ref"] for c in fam["child_ref_list"]}
        assert child_handles == {"h_pe_testor", "h_pe_testiane"}

    def test_test_family_no_parents(self, db):
        fam = db.get("family", "h_fa_test")
        assert fam["father_handle"] == ""
        assert fam["mother_handle"] == ""

    def test_test_family_relationship(self, db):
        fam = db.get("family", "h_fa_test")
        assert fam["relationship"] == "Unknown"

    def test_testor_birth_event(self, db):
        testor = db.get("person", "h_pe_testor")
        assert testor["birth_ref_index"] == 0
        assert testor["event_ref_list"][0]["ref"] == "h_ev_birth_testor"

    def test_testiane_birth_event(self, db):
        testiane = db.get("person", "h_pe_testiane")
        assert testiane["birth_ref_index"] == 0
        assert testiane["event_ref_list"][0]["ref"] == "h_ev_birth_testiane"


# ===========================================================================
# GQL filtering
# ===========================================================================


class TestGqlFiltering:
    @pytest.mark.asyncio
    async def test_gql_gender_male(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_PEOPLE, params={"gql": "gender = 1", "pagesize": 100}
        )
        assert all(p["gender"] == 1 for p in result)
        ids = {p["gramps_id"] for p in result}
        assert {"I0001", "I0003", "I0005"}.issubset(ids)  # John, James, Testor

    @pytest.mark.asyncio
    async def test_gql_gender_female(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_PEOPLE, params={"gql": "gender = 0", "pagesize": 100}
        )
        assert all(p["gender"] == 0 for p in result)
        ids = {p["gramps_id"] for p in result}
        assert {"I0002", "I0006"}.issubset(ids)  # Jane, Testiane

    @pytest.mark.asyncio
    async def test_gql_surname_contains(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_PEOPLE,
            params={"gql": "primary_name.surname_list[0].surname ~ Smith", "pagesize": 100},
        )
        ids = {p["gramps_id"] for p in result}
        assert "I0001" in ids   # John Smith
        assert "I0003" in ids   # James Smith
        assert "I0005" not in ids  # Testor von Test

    @pytest.mark.asyncio
    async def test_gql_gramps_id_equals(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_PEOPLE,
            params={"gql": "gramps_id = I0001", "pagesize": 100},
        )
        assert len(result) == 1
        assert result[0]["gramps_id"] == "I0001"

    @pytest.mark.asyncio
    async def test_gql_media_length(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_PEOPLE,
            params={"gql": "media_list.length > 0", "pagesize": 100},
        )
        assert len(result) == 1
        assert result[0]["gramps_id"] == "I0001"  # only John has a photo

    @pytest.mark.asyncio
    async def test_gql_and(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_PEOPLE,
            params={
                "gql": "gender = 1 and primary_name.surname_list[0].surname ~ Smith",
                "pagesize": 100,
            },
        )
        ids = {p["gramps_id"] for p in result}
        assert "I0001" in ids   # John Smith (M)
        assert "I0003" in ids   # James Smith (M)
        assert "I0002" not in ids  # Jane Doe (F)

    @pytest.mark.asyncio
    async def test_gql_or(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_PEOPLE,
            params={
                "gql": "gramps_id = I0001 or gramps_id = I0002",
                "pagesize": 100,
            },
        )
        ids = {p["gramps_id"] for p in result}
        assert ids == {"I0001", "I0002"}

    @pytest.mark.asyncio
    async def test_gql_empty_returns_all(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_PEOPLE, params={"gql": "", "pagesize": 100}
        )
        assert len(result) == 6

    @pytest.mark.asyncio
    async def test_gql_address_city(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_PEOPLE,
            params={"gql": "address_list[0].city ~ Testhausen", "pagesize": 100},
        )
        ids = {p["gramps_id"] for p in result}
        assert "I0005" in ids   # Testor
        assert "I0006" in ids   # Testiane
        assert "I0001" not in ids  # John has no address


# ===========================================================================
# Ancestors / descendants traversal
# ===========================================================================


class TestTraversal:
    @pytest.mark.asyncio
    async def test_descendants_report_filename(self, client):
        import json
        result = await client.make_api_call(
            ApiCalls.POST_REPORT_FILE,
            params={"options": json.dumps({"pid": "I0001", "off": "html", "gen": "3"})},
            report_id="descend_report",
        )
        assert "file_name" in result
        assert result["file_name"].startswith("direct_descend_report_")

    @pytest.mark.asyncio
    async def test_descendants_contains_child(self, client):
        import json
        gen = await client.make_api_call(
            ApiCalls.POST_REPORT_FILE,
            params={"options": json.dumps({"pid": "I0001", "off": "html", "gen": "3"})},
            report_id="descend_report",
        )
        report = await client.make_api_call(
            ApiCalls.GET_REPORT_PROCESSED,
            report_id="descend_report",
            filename=gen["file_name"],
        )
        html = report["raw_content"]
        assert "James Smith" in html
        assert "I0003" in html

    @pytest.mark.asyncio
    async def test_descendants_header(self, client):
        import json
        gen = await client.make_api_call(
            ApiCalls.POST_REPORT_FILE,
            params={"options": json.dumps({"pid": "I0001", "off": "html", "gen": "3"})},
            report_id="descend_report",
        )
        report = await client.make_api_call(
            ApiCalls.GET_REPORT_PROCESSED,
            report_id="descend_report",
            filename=gen["file_name"],
        )
        assert "John Robert Smith" in report["raw_content"]

    @pytest.mark.asyncio
    async def test_ancestors_contains_parents(self, client):
        import json
        gen = await client.make_api_call(
            ApiCalls.POST_REPORT_FILE,
            params={"options": json.dumps({"pid": "I0003", "off": "html", "maxgen": "3"})},
            report_id="ancestor_report",
        )
        report = await client.make_api_call(
            ApiCalls.GET_REPORT_PROCESSED,
            report_id="ancestor_report",
            filename=gen["file_name"],
        )
        html = report["raw_content"]
        assert "John Robert Smith" in html  # father
        assert "Jane Doe" in html           # mother

    @pytest.mark.asyncio
    async def test_ancestors_no_parents_message(self, client):
        import json
        gen = await client.make_api_call(
            ApiCalls.POST_REPORT_FILE,
            params={"options": json.dumps({"pid": "I0001", "off": "html", "maxgen": "3"})},
            report_id="ancestor_report",
        )
        report = await client.make_api_call(
            ApiCalls.GET_REPORT_PROCESSED,
            report_id="ancestor_report",
            filename=gen["file_name"],
        )
        assert "No ancestors found" in report["raw_content"]

    @pytest.mark.asyncio
    async def test_report_cache_idempotent_get(self, client):
        """GET_REPORT_PROCESSED is idempotent — a second call returns the same report."""
        import json
        gen = await client.make_api_call(
            ApiCalls.POST_REPORT_FILE,
            params={"options": json.dumps({"pid": "I0001", "off": "html", "gen": "1"})},
            report_id="descend_report",
        )
        filename = gen["file_name"]
        result1 = await client.make_api_call(
            ApiCalls.GET_REPORT_PROCESSED,
            report_id="descend_report",
            filename=filename,
        )
        result2 = await client.make_api_call(
            ApiCalls.GET_REPORT_PROCESSED,
            report_id="descend_report",
            filename=filename,
        )
        assert result1["raw_content"] == result2["raw_content"]

    @pytest.mark.asyncio
    async def test_unsupported_report_id_raises(self, client):
        with pytest.raises(GrampsAPIError, match="not supported"):
            await client.make_api_call(
                ApiCalls.POST_REPORT_FILE,
                params={"options": "{}"},
                report_id="some_other_report",
            )


# ===========================================================================
# Timeline: GET_PERSON_TIMELINE / GET_FAMILY_TIMELINE
# ===========================================================================


class TestTimeline:
    @pytest.mark.asyncio
    async def test_person_timeline_is_list(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_PERSON_TIMELINE, handle="h_pe_john"
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_person_timeline_own_events(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_PERSON_TIMELINE, handle="h_pe_john"
        )
        types = {e["type"] for e in result}
        assert "Birth" in types
        assert "Death" in types

    @pytest.mark.asyncio
    async def test_person_timeline_includes_family_event(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_PERSON_TIMELINE, handle="h_pe_john"
        )
        types = {e["type"] for e in result}
        assert "Marriage" in types

    @pytest.mark.asyncio
    async def test_person_timeline_self_relationship(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_PERSON_TIMELINE, handle="h_pe_john"
        )
        birth = next(e for e in result if e["type"] == "Birth")
        assert birth["person"]["relationship"] == "self"
        assert birth["handle"] == "h_ev_birth_john"
        assert birth["gramps_id"] == "E0001"

    @pytest.mark.asyncio
    async def test_person_timeline_place_display_name(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_PERSON_TIMELINE, handle="h_pe_john"
        )
        birth = next(e for e in result if e["type"] == "Birth")
        assert birth["place"]["display_name"] == "Berlin, Germany"

    @pytest.mark.asyncio
    async def test_person_timeline_sorted_birth_before_death(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_PERSON_TIMELINE, handle="h_pe_john"
        )
        types = [e["type"] for e in result]
        assert types.index("Birth") < types.index("Death")

    @pytest.mark.asyncio
    async def test_person_timeline_marriage_shows_spouse(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_PERSON_TIMELINE, handle="h_pe_john"
        )
        marriage = next(e for e in result if e["type"] == "Marriage")
        assert marriage["person"]["relationship"] == "spouse"
        assert marriage["person"]["gramps_id"] == "I0002"  # Jane

    @pytest.mark.asyncio
    async def test_person_timeline_missing_handle_raises(self, client):
        with pytest.raises(GrampsAPIError, match="not found"):
            await client.make_api_call(
                ApiCalls.GET_PERSON_TIMELINE, handle="nonexistent"
            )

    @pytest.mark.asyncio
    async def test_family_timeline_is_list(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_FAMILY_TIMELINE, handle="h_fa_smith"
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_family_timeline_includes_marriage(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_FAMILY_TIMELINE, handle="h_fa_smith"
        )
        types = {e["type"] for e in result}
        assert "Marriage" in types

    @pytest.mark.asyncio
    async def test_family_timeline_includes_parent_events(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_FAMILY_TIMELINE, handle="h_fa_smith"
        )
        # Marriage + John(Birth+Death) + Jane(Birth) = 4 items
        assert len(result) >= 4

    @pytest.mark.asyncio
    async def test_family_timeline_father_relationship(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_FAMILY_TIMELINE, handle="h_fa_smith"
        )
        father_events = [e for e in result if e["person"].get("relationship") == "father"]
        assert len(father_events) >= 1
        assert all(e["person"]["gramps_id"] == "I0001" for e in father_events)

    @pytest.mark.asyncio
    async def test_family_timeline_sorted(self, client):
        result = await client.make_api_call(
            ApiCalls.GET_FAMILY_TIMELINE, handle="h_fa_smith"
        )
        # John born 1950, Jane born 1952, married 1975, John died 2020
        years = [int(e["date"]) for e in result if e["date"].isdigit()]
        assert years == sorted(years)


# ===========================================================================
# open_database / close_database lifecycle for XML/gpkg backend
# ===========================================================================


class TestXmlOpenCloseLifecycle:
    def test_open_gpkg_via_factory(self, gpkg_path):
        """open_database() returns a GrampsDirectClient for .gpkg paths."""
        from gramps_mcp.client import open_database, close_database
        client, locked_by = open_database(gpkg_path)
        assert client is not None
        assert locked_by == ""  # no lock for XML files
        close_database()

    def test_open_gpkg_mode_is_readonly(self, gpkg_path):
        """GrampsDirectClient has no _conn attribute (not SQLite)."""
        from gramps_mcp.client import open_database, close_database
        client, _ = open_database(gpkg_path)
        assert not hasattr(client._db, "_conn")
        close_database()

    def test_close_gpkg_returns_path(self, gpkg_path):
        """close_database() returns the path that was open."""
        from gramps_mcp.client import open_database, close_database
        open_database(gpkg_path)
        path = close_database()
        assert path == gpkg_path

    def test_close_gpkg_no_lock_file_created(self, gpkg_path):
        """Opening a .gpkg must not create a lock file alongside it."""
        import os
        from gramps_mcp.client import open_database, close_database
        lock_path = os.path.join(os.path.dirname(gpkg_path), "lock")
        open_database(gpkg_path)
        assert not os.path.exists(lock_path), "Lock file must not be created for XML"
        close_database()

    def test_get_client_after_open(self, gpkg_path):
        """get_client() returns the singleton set by open_database."""
        from gramps_mcp.client import open_database, close_database, get_client
        opened_client, _ = open_database(gpkg_path)
        fetched = get_client()
        assert fetched is opened_client
        close_database()

    def test_get_client_after_close_raises(self, gpkg_path, monkeypatch):
        """After close_database, get_client raises if no env var is set."""
        from gramps_mcp.client import open_database, close_database, get_client, GrampsAPIError
        import gramps_mcp.client as client_mod
        open_database(gpkg_path)
        close_database()
        # Patch settings to have no backend configured
        class _EmptySettings:
            use_direct_backend = False
            gramps_api_url = None
            gramps_db_path = None
        monkeypatch.setattr(client_mod, "get_settings", lambda: _EmptySettings())
        with pytest.raises(GrampsAPIError, match="No database connected"):
            get_client()

    @pytest.mark.asyncio
    async def test_write_raises_for_xml(self, gpkg_path):
        """POST operations raise GrampsAPIError for the read-only XML backend."""
        from gramps_mcp.client import open_database, close_database, GrampsAPIError
        client, _ = open_database(gpkg_path)
        with pytest.raises(GrampsAPIError, match="write access"):
            await client.make_api_call(ApiCalls.POST_PEOPLE, params={})
        close_database()
