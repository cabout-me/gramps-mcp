"""
Integration tests for data management tools using real Gramps Web API.

Tests all 8 save tools: save_person, save_family, save_event, save_place,
save_source, save_citation, save_note, and save_media tools.
These tests require a working Gramps Web API instance with valid credentials.
Only tests actual API integration - Pydantic validation is tested elsewhere.
"""

import pytest

from src.gramps_mcp.tools.data_management import (
    create_citation_tool,
    create_event_tool,
    create_family_tool,
    create_media_tool,
    create_note_tool,
    create_person_tool,
    create_place_tool,
    create_repository_tool,
    create_source_tool,
)

# Store handles for chaining tests following proper Gramps workflow
test_note_handle = None
test_media_handle = None
test_repository_handle = None
test_source_handle = None
test_citation_handle = None 
test_place_handle = None
test_event_handle = None
test_person_handles = []


class TestCreateNoteTool:
    """Test create_note_tool functionality - First in workflow."""

    @pytest.mark.asyncio
    async def test_create_note_success(self):
        """Test successful note creation with proper text structure and type."""
        global test_note_handle

        result = await create_note_tool(
            {
                "text": "This is a test research note about the family history.",
                "type": "Research",
            }
        )

        print("\n--- SAVE NOTE CREATE SUCCESS RESULT ---")
        print(result[0].text)
        print("--- END ---\n")

        text = result[0].text
        assert "Error:" not in text, f"Expected success but got error: {text}"
        assert "successfully" in text.lower()
        
        # Assert all required fields from usage guide are in output
        assert "This is a test research note about the family history." in text, f"Expected note text in output but got: {text}"
        assert "Research" in text, f"Expected note type 'Research' in output but got: {text}"
        
        # Extract note handle for use in subsequent tests
        import re
        handle_match = re.search(r"\[([a-f0-9]+)\]", text)
        if handle_match:
            test_note_handle = handle_match.group(1)
            print(f"Extracted note handle: {test_note_handle}")
        else:
            pytest.fail("Could not extract note handle for chaining tests")


class TestCreateMediaTool:
    """Test create_media_tool functionality - Second in workflow."""

    @pytest.mark.asyncio
    async def test_create_media_success(self):
        """Test successful media creation with actual file upload."""
        global test_media_handle

        result = await create_media_tool(
            {
                "file_location": "tests/sample/33SQ-GP8N-NLK.jpg",
                "desc": "Birth register page showing John Smith entry",
                "date": {
                    "dateval": [15, 1, 2024, False],
                    "quality": 0,
                    "modifier": 0
                }
            }
        )

        print("\n--- SAVE MEDIA CREATE RESULT ---")
        print(repr(result[0].text))
        print("--- END ---\n")
        
        # Debug: Show what we sent
        print("\n--- DEBUG: Parameters sent ---")
        print("file_location: tests/sample/33SQ-GP8N-NLK.jpg")
        print("desc: Birth register page showing John Smith entry")
        print("--- END DEBUG ---\n")

        text = result[0].text
        assert "Error:" not in text, f"Expected success but got error: {text}"
        assert "successfully" in text.lower()
        assert "media" in text.lower()
        
        # Assert all required fields from usage guide are in output
        # New format: file type - gramps id - handle \n desc - date
        assert "Birth register page showing John Smith entry" in text, f"Expected desc in output but got: {text}"
        # Should show proper image MIME type
        assert "image/jpeg" in text, f"Expected image MIME type but got: {text}"
        # Assert formatted date from date_handler (not raw dateval components)
        assert "15 January 2024" in text, f"Expected formatted date '15 January 2024' in output but got: {text}"
        
        # Extract media handle for use in subsequent tests
        import re
        handle_match = re.search(r"\[([a-f0-9]+)\]", text)
        if handle_match:
            test_media_handle = handle_match.group(1)
            print(f"Extracted media handle: {test_media_handle}")
        else:
            pytest.fail("Could not extract media handle for chaining tests")

class TestCreateRepositoryTool:
    """Test create_repository_tool functionality - Third in workflow."""

    @pytest.mark.asyncio
    async def test_create_repository_success(self):
        """Test successful repository creation using note handle from previous test."""
        global test_repository_handle, test_note_handle

        # Ensure we have a note handle from the previous test
        if not test_note_handle:
            pytest.fail("No note handle available from previous test - run tests in order")

        result = await create_repository_tool(
            {
                "name": "National Archives - Boston Branch",
                "type": "Archive",
                "urls": [
                    {
                        "type": "Web Home",
                        "path": "https://www.archives.gov/boston",
                        "desc": "Official website"
                    }
                ],
                "note_list": [test_note_handle]
            }
        )

        print("\n--- SAVE REPOSITORY CREATE SUCCESS RESULT ---")
        print(result[0].text)
        print("--- END ---\n")

        text = result[0].text
        assert "Error:" not in text, f"Expected success but got error: {text}"
        assert "successfully" in text.lower()
        
        # Assert all required fields from usage guide are in output
        assert "National Archives - Boston Branch" in text, f"Expected repository name (required) in output but got: {text}"
        assert "Archive" in text, f"Expected repository type (required) in output but got: {text}"
        
        # Assert optional fields that were provided
        assert "https://www.archives.gov/boston" in text, f"Expected URL path in output but got: {text}"
        assert "Official website" in text, f"Expected URL description in output but got: {text}"
        # Check that attached notes shows some note reference
        assert "Attached notes: N" in text, f"Expected note reference after 'Attached notes:' in output but got: {text}"
        
        # Extract repository handle for use in subsequent tests
        import re
        # Repository handler format: "Archive: Name - ID - [handle]"
        handle_match = re.search(r"- \[([^\]]+)\]", text)
        if handle_match:
            test_repository_handle = handle_match.group(1)
            print(f"Extracted repository handle: {test_repository_handle}")
        else:
            pytest.fail("Could not extract repository handle for chaining tests")


class TestCreateSourceTool:
    """Test create_source_tool functionality - Fourth in workflow."""

    @pytest.mark.asyncio
    async def test_create_source_success(self):
        """Test successful source creation using repository and media handles."""
        global test_source_handle, test_repository_handle, test_media_handle, test_note_handle

        # Ensure we have handles from previous tests
        if not test_repository_handle:
            pytest.fail("No repository handle available from previous test - run tests in order")

        result = await create_source_tool(
            {
                "title": "Birth Register 1850-1860",
                "reporef_list": [
                    {
                        "ref": test_repository_handle
                    }
                ],
                "author": "City Clerk's Office",
                "pubinfo": "Boston City Records, Volume 12",
                "media_list": [{"ref": test_media_handle}] if test_media_handle else [],
                "note_list": [test_note_handle] if test_note_handle else []
            }
        )

        print("\n--- SAVE SOURCE CREATE SUCCESS RESULT ---")
        print(result[0].text)
        print("--- END ---\n")

        text = result[0].text
        assert "Error:" not in text, f"Expected success but got error: {text}"
        assert "successfully" in text.lower()
        
        # Assert all required fields from usage guide are in output
        assert "Birth Register 1850-1860" in text, f"Expected source title (required) in output but got: {text}"
        assert "National Archives - Boston Branch" in text, f"Expected repository reference (required) in output but got: {text}"
        
        # Assert optional fields that were provided
        assert "City Clerk's Office" in text, f"Expected author in output but got: {text}"
        assert "Boston City Records, Volume 12" in text, f"Expected publication info in output but got: {text}"
        # Should show linked media and note if present
        if "image/" in text:
            assert "Birth register page showing John Smith entry" in text, f"Expected linked media description in output but got: {text}"
        if "Research" in text:
            assert "Research" in text, f"Expected linked note type in output but got: {text}"
        
        # Extract source handle for use in subsequent tests
        import re
        handle_match = re.search(r"\[([a-f0-9]+)\]", text)
        if handle_match:
            test_source_handle = handle_match.group(1)
            print(f"Extracted source handle: {test_source_handle}")
        else:
            pytest.fail("Could not extract source handle for chaining tests")


class TestCreateCitationTool:
    """Test create_citation_tool functionality - Fifth in workflow."""

    @pytest.mark.asyncio
    async def test_create_citation_success(self):
        """Test successful citation creation using source handle."""
        global test_citation_handle, test_source_handle, test_media_handle, test_note_handle

        # Ensure we have a source handle from previous test
        if not test_source_handle:
            pytest.fail("No source handle available from previous test - run tests in order")
        
        result = await create_citation_tool(
            {
                "source_handle": test_source_handle,
                "page": "Page 45, Entry 23",
                "date": {
                    "dateval": [15, 1, 2024, False],
                    "quality": 1,  # estimated
                    "modifier": 3  # about
                },
                "media_list": [{"ref": test_media_handle}] if test_media_handle else [],
                "note_list": [test_note_handle] if test_note_handle else []
            }
        )

        print("\n--- SAVE CITATION CREATE SUCCESS RESULT ---")
        print(result[0].text)
        print("--- END ---\n")

        text = result[0].text
        assert "Error:" not in text, f"Expected success but got error: {text}"
        assert "successfully" in text.lower()
        
        # Assert all required fields from usage guide are in output
        assert "Birth Register 1850-1860" in text, f"Expected source reference (required) in output but got: {text}"
        
        # Assert optional fields that were provided
        assert "Page 45, Entry 23" in text, f"Expected citation page in output but got: {text}"
        # Assert date shows full date with modifier and quality
        # Date format: [2024, 1, 15, False] with quality=1 (estimated) and modifier=3 (about)
        assert "about 15 January 2024 (estimated)" in text, f"Expected full citation date with modifier and quality in output but got: {text}"
        # Should show linked media and note if present
        if "image/" in text:
            assert "Birth register page showing John Smith entry" in text, f"Expected linked media description in output but got: {text}"
        if "Research" in text:
            assert "Research" in text, f"Expected linked note type in output but got: {text}"
        
        # Extract citation handle for use in subsequent tests
        import re
        handle_match = re.search(r"\[([a-f0-9]+)\]", text)
        if handle_match:
            test_citation_handle = handle_match.group(1)
            print(f"Extracted citation handle: {test_citation_handle}")
        else:
            pytest.fail("Could not extract citation handle for chaining tests")


class TestCreatePlaceTool:
    """Test create_place_tool functionality - Sixth in workflow."""

    @pytest.mark.asyncio
    async def test_create_place_success(self):
        """Test successful place creation with proper hierarchy."""
        global test_place_handle

        # First create country (top level)
        country_result = await create_place_tool(
            {
                "name": {"value": "United States"},
                "place_type": "Country"
            }
        )
        
        print("\n--- Country creation result ---")
        print(country_result[0].text)
        print("--- END ---\n")
        
        # Extract country handle
        import re
        country_handle_match = re.search(r"\[([a-f0-9]+)\]", country_result[0].text)
        country_handle = country_handle_match.group(1) if country_handle_match else None
        
        if not country_handle:
            pytest.fail("Could not extract country handle")

        # Create state enclosed by country
        state_result = await create_place_tool(
            {
                "name": {"value": "Massachusetts"},
                "place_type": "State",
                "placeref_list": [{"ref": country_handle}]
            }
        )
        
        # Extract state handle
        state_handle_match = re.search(r"\[([a-f0-9]+)\]", state_result[0].text)
        state_handle = state_handle_match.group(1) if state_handle_match else None
        
        if not state_handle:
            pytest.fail("Could not extract state handle")

        # Create city enclosed by state
        result = await create_place_tool(
            {
                "name": {"value": "Boston"},
                "place_type": "City",
                "placeref_list": [{"ref": state_handle}],
                "urls": [
                    {
                        "type": "Web Home",
                        "path": "https://www.boston.gov",
                        "description": "Official city website"
                    }
                ]
            }
        )

        print("\n--- SAVE PLACE CREATE SUCCESS RESULT ---")
        print(result[0].text)
        print("--- END ---\n")

        text = result[0].text
        assert "Error:" not in text, f"Expected success but got error: {text}"
        assert "successfully" in text.lower()
        
        # Assert all required fields from usage guide are in output
        assert "Boston" in text, f"Expected place title (required) in output but got: {text}"
        assert "City" in text, f"Expected place type (required) in output but got: {text}"
        assert "Massachusetts" in text, f"Expected enclosed_by reference in output but got: {text}"
        
        # Assert optional fields that were provided
        urls = re.findall(r'(https?://[^\s"\',]+)', text)
        assert "https://www.boston.gov" in urls, f"Expected URL 'https://www.boston.gov' in output URLs {urls} but got: {text}"
        assert "Official city website" in text, f"Expected URL description in output but got: {text}"
        
        # Extract place handle for use in subsequent tests
        place_handle_match = re.search(r"\[([a-f0-9]+)\]", text)
        if place_handle_match:
            test_place_handle = place_handle_match.group(1)
            print(f"Extracted place handle: {test_place_handle}")
        else:
            pytest.fail("Could not extract place handle for chaining tests")


class TestCreateEventTool:
    """Test create_event_tool functionality - Seventh in workflow."""

    @pytest.mark.asyncio
    async def test_create_event_success(self):
        """Test successful event creation using citation and place handles."""
        global test_event_handle, test_citation_handle, test_place_handle

        # Ensure we have handles from previous tests
        if not test_citation_handle:
            pytest.fail("No citation handle available from previous test - run tests in order")

        result = await create_event_tool(
            {
                "type": "Birth",
                "citation_list": [test_citation_handle],
                "date": {
                    "dateval": [15, 6, 1878, False],
                    "quality": 0,
                    "modifier": 0
                },
                "place": test_place_handle if test_place_handle else None
            }
        )

        print("\n--- SAVE EVENT CREATE SUCCESS RESULT ---")
        print(result[0].text)
        print("--- END ---\n")

        text = result[0].text
        assert "Error:" not in text, f"Expected success but got error: {text}"
        assert "successfully" in text.lower()
        
        # Assert all required fields from usage guide are in output
        assert "Birth" in text, f"Expected type (required) in output but got: {text}"
        # Assert citation is referenced by gramps_id (will be different each run)
        assert "Attached citations: C" in text, f"Expected citation gramps_id (required) in output but got: {text}"
        
        # Assert optional fields that were provided
        # Assert formatted date (15 June 1878)
        assert "15 June 1878" in text, f"Expected formatted event date in output but got: {text}"
        # Should show linked place if present
        assert "Boston" in text, f"Expected linked place in output but got: {text}"
        
        # Extract event handle for use in subsequent tests
        import re
        handle_match = re.search(r"\[([a-f0-9]+)\]", text)
        if handle_match:
            test_event_handle = handle_match.group(1)
            print(f"Extracted event handle: {test_event_handle}")
        else:
            pytest.fail("Could not extract event handle for chaining tests")


class TestCreatePersonTool:
    """Test create_person_tool functionality - Eighth in workflow."""

    @pytest.mark.asyncio
    async def test_create_person_success(self):
        """Test successful person creation using proper structure and linking events."""
        global test_person_handles, test_event_handle, test_media_handle, test_note_handle

        result = await create_person_tool(
            {
                "primary_name": {
                    "first_name": "John",
                    "surname_list": [
                        {
                            "surname": "Smith",
                            "primary": True
                        }
                    ]
                },
                "gender": 1,  # Male
                "event_ref_list": [
                    {
                        "ref": test_event_handle,
                        "role": "Primary"
                    }
                ] if test_event_handle else [],
                "media_list": [{"ref": test_media_handle}] if test_media_handle else [],
                "note_list": [test_note_handle] if test_note_handle else [],
                "urls": [
                    {
                        "type": "Web Home",
                        "path": "https://familysearch.org/person/123",
                        "description": "FamilySearch profile"
                    }
                ]
            }
        )

        print("\n--- SAVE PERSON CREATE SUCCESS RESULT ---")
        print(result[0].text)
        print("--- END ---\n")

        text = result[0].text
        assert "Error:" not in text, f"Expected success but got error: {text}"
        assert "successfully" in text.lower()
        
        # Assert all required fields from usage guide are in output
        assert "John" in text, f"Expected primary_name first_name (required) in output but got: {text}"
        assert "Smith" in text, f"Expected primary_name surname (required) in output but got: {text}"
        # Gender 1 = Male should be shown as (M)
        assert "(M)" in text, f"Expected gender (M) in output but got: {text}"
        
        # Assert optional fields that were provided
        # Should show linked event with role
        if "Birth" in text:
            assert "Birth" in text, f"Expected linked event in output but got: {text}"
            assert "Primary" in text, f"Expected event role in output but got: {text}"
        # Should show linked media and note if present
        if "image/" in text:
            assert "Birth register page showing John Smith entry" in text, f"Expected linked media description in output but got: {text}"
        if "Research" in text:
            assert "Research" in text, f"Expected linked note type in output but got: {text}"
        # Should show URLs
        assert "https://familysearch.org/person/123" in text, f"Expected URL path in output but got: {text}"
        assert "FamilySearch profile" in text, f"Expected URL description in output but got: {text}"
        
        # Extract person handle for use in family test
        import re
        handle_match = re.search(r"\[([a-f0-9]+)\]", text)
        if handle_match:
            john_handle = handle_match.group(1)
            test_person_handles.append(john_handle)
            print(f"Extracted person handle: {john_handle}")
        else:
            pytest.fail("Could not extract person handle for chaining tests")

    @pytest.mark.asyncio
    async def test_create_second_person_success(self):
        """Test creation of second person for family test."""
        global test_person_handles, test_media_handle, test_note_handle

        result = await create_person_tool(
            {
                "primary_name": {
                    "first_name": "Mary",
                    "surname_list": [
                        {
                            "surname": "Johnson",
                            "primary": True
                        }
                    ]
                },
                "gender": 0,  # Female
                "media_list": [{"ref": test_media_handle}] if test_media_handle else [],
                "note_list": [test_note_handle] if test_note_handle else [],
                "urls": [
                    {
                        "type": "Web Home", 
                        "path": "https://familysearch.org/person/456",
                        "description": "FamilySearch profile"
                    }
                ]
            }
        )

        print("\n--- SAVE SECOND PERSON CREATE SUCCESS RESULT ---")
        print(result[0].text)
        print("--- END ---\n")

        text = result[0].text
        assert "Error:" not in text, f"Expected success but got error: {text}"
        assert "successfully" in text.lower()
        
        # Assert all required fields from usage guide are in output
        assert "Mary" in text, f"Expected primary_name first_name (required) in output but got: {text}"
        assert "Johnson" in text, f"Expected primary_name surname (required) in output but got: {text}"
        # Gender 0 = Female should be shown as (F)
        assert "(F)" in text, f"Expected gender (F) in output but got: {text}"
        
        # Assert optional fields that were provided
        # Should show linked media and note if present
        if "image/" in text:
            assert "Birth register page showing John Smith entry" in text, f"Expected linked media description in output but got: {text}"
        if "Research" in text:
            assert "Research" in text, f"Expected linked note type in output but got: {text}"
        # Should show URLs
        assert "https://familysearch.org/person/456" in text, f"Expected URL path in output but got: {text}"
        assert "FamilySearch profile" in text, f"Expected URL description in output but got: {text}"
        
        # Extract person handle for use in family test
        import re
        handle_match = re.search(r"\[([a-f0-9]+)\]", text)
        if handle_match:
            mary_handle = handle_match.group(1)
            test_person_handles.append(mary_handle)
            print(f"Extracted second person handle: {mary_handle}")
        else:
            pytest.fail("Could not extract second person handle for chaining tests")


class TestCreateFamilyTool:
    """Test create_family_tool functionality - Last in workflow."""

    @pytest.mark.asyncio
    async def test_create_family_success(self):
        """Test successful family creation using person handles from previous tests."""
        global test_person_handles, test_media_handle, test_note_handle

        # Ensure we have person handles from previous tests
        if len(test_person_handles) < 2:
            pytest.fail("Need at least 2 person handles from previous tests - run tests in order")
        
        father_handle = test_person_handles[0]  # John Smith
        mother_handle = test_person_handles[1]  # Mary Johnson
        
        result = await create_family_tool(
            {
                "father_handle": father_handle,
                "mother_handle": mother_handle,
                "media_list": [{"ref": test_media_handle}] if test_media_handle else [],
                "note_list": [test_note_handle] if test_note_handle else [],
                "urls": [
                    {
                        "type": "Web Home",
                        "path": "https://familysearch.org/family/789",
                        "description": "FamilySearch family record"
                    }
                ]
            }
        )

        print("\n--- SAVE FAMILY CREATE SUCCESS RESULT ---")
        print(result[0].text)
        print("--- END ---\n")

        text = result[0].text
        assert "Error:" not in text, f"Expected success but got error: {text}"
        assert "successfully" in text.lower()
        
        # Assert required fields from usage guide are in output (at least one parent)
        # Father and mother handles are both optional, but at least one should be present
        assert "John" in text or "Smith" in text, f"Expected father reference in output but got: {text}"
        assert "Mary" in text or "Johnson" in text, f"Expected mother reference in output but got: {text}"
        
        # Assert optional fields that were provided
        # Should show linked media and note if present
        if "image/" in text:
            assert "Birth register page showing John Smith entry" in text, f"Expected linked media description in output but got: {text}"
        if "Research" in text:
            assert "Research" in text, f"Expected linked note type in output but got: {text}"
        # Should show URLs (new format: path - description)
        assert "https://familysearch.org/family/789" in text, f"Expected URL path in output but got: {text}"
        assert "FamilySearch family record" in text, f"Expected URL description in output but got: {text}"


# Removed validation tests - Pydantic handles input validation automatically
# These tests focus only on actual Gramps Web API integration
