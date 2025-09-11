"""
Integration tests for basic search tools using real Gramps API.

Tests search_people, search_families, search_events, search_places, 
search_sources, search_media, and search_all tools.
"""


import pytest
from dotenv import load_dotenv
from mcp.types import TextContent

from src.gramps_mcp.tools.search_basic import (
    find_anything_tool,
    find_type_tool,
)

# Load environment variables
load_dotenv()


class TestFindPersonTool:
    """Test find_type_tool functionality for person with real API."""
    
    @pytest.mark.asyncio
    async def test_find_person(self):
        """Test people search with GQL."""
        result = await find_type_tool({
            "type": "person",
            "gql": "primary_name.first_name ~ \"John\"",
            "max_results": 3,
        })
        
        print("\n--- FIND PERSON RESULT ---")
        print(result[0].text)
        print("--- END ---\n")
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "error" not in result[0].text.lower(), f"Error found in response: {result[0].text}"
        assert "Found" in result[0].text or "No people found" in result[0].text
        
        # Assert max_results is respected - count actual result entries
        if "Found" in result[0].text and "No people found" not in result[0].text:
            # Count the number of "• **" entries which indicate individual results
            result_count = result[0].text.count("• **")
            assert result_count <= 3, f"Expected max 3 results, got {result_count}"


class TestFindFamilyTool:
    """Test find_type_tool functionality for family with real API."""
    
    @pytest.mark.asyncio
    async def test_find_family(self):
        """Test families search with GQL."""
        result = await find_type_tool({
            "type": "family",
            "gql": "father_handle.get_person.primary_name.surname_list.any.surname ~ \"Smith\"",
            "max_results": 3
        })
        
        print("\n--- FIND FAMILY RESULT ---")
        print(result[0].text)
        print("--- END ---\n")
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "error" not in result[0].text.lower(), f"Error found in response: {result[0].text}"
        assert "Found" in result[0].text or "No families found" in result[0].text
        
        # Assert max_results is respected - count actual result entries
        if "Found" in result[0].text and "No families found" not in result[0].text:
            # Count the number of "• **" entries which indicate individual results
            result_count = result[0].text.count("• **")
            assert result_count <= 3, f"Expected max 3 results, got {result_count}"


class TestFindEventTool:
    """Test find_type_tool functionality for event with real API."""
    
    @pytest.mark.asyncio
    async def test_find_event(self):
        """Test events search with GQL."""
        result = await find_type_tool({
            "type": "event",
            "gql": "date.dateval[2] > 1800",
            "max_results": 3
        })
        
        print("\n--- FIND EVENT RESULT ---")
        print(result[0].text)
        print("--- END ---\n")
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "error" not in result[0].text.lower(), f"Error found in response: {result[0].text}"
        assert "Found" in result[0].text or "No events found" in result[0].text
        
        # Assert max_results is respected - count actual result entries
        if "Found" in result[0].text and "No events found" not in result[0].text:
            # Count the number of "• **" entries which indicate individual results
            result_count = result[0].text.count("• **")
            assert result_count <= 3, f"Expected max 3 results, got {result_count}"


class TestFindPlaceTool:
    """Test find_type_tool functionality for place with real API."""
    
    @pytest.mark.asyncio
    async def test_find_place(self):
        """Test places search with GQL."""
        result = await find_type_tool({
            "type": "place",
            "gql": "name.value ~ \"Boston\"",
            "max_results": 3
        })
        
        print("\n--- FIND PLACE RESULT ---")
        print(result[0].text)
        print("--- END ---\n")
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "error" not in result[0].text.lower(), f"Error found in response: {result[0].text}"
        assert "Found" in result[0].text or "No places found" in result[0].text
        
        # Assert max_results is respected - count actual result entries
        if "Found" in result[0].text and "No places found" not in result[0].text:
            # Count the number of "• **" entries which indicate individual results
            result_count = result[0].text.count("• **")
            assert result_count <= 3, f"Expected max 3 results, got {result_count}"


class TestFindSourceTool:
    """Test find_type_tool functionality for source with real API."""
    
    @pytest.mark.asyncio
    async def test_find_source(self):
        """Test sources search with GQL."""
        result = await find_type_tool({
            "type": "source",
            "gql": "title ~ \"census\"",
            "max_results": 3
        })
        
        print("\n--- FIND SOURCE RESULT ---")
        print(result[0].text)
        print("--- END ---\n")
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "error" not in result[0].text.lower(), f"Error found in response: {result[0].text}"
        assert "Found" in result[0].text or "No sources found" in result[0].text
        
        # Assert max_results is respected - count actual result entries
        if "Found" in result[0].text and "No sources found" not in result[0].text:
            # Count the number of "• **" entries which indicate individual results
            result_count = result[0].text.count("• **")
            assert result_count <= 3, f"Expected max 3 results, got {result_count}"


class TestFindRepositoryTool:
    """Test find_type_tool functionality for repository with real API."""
    
    @pytest.mark.asyncio
    async def test_find_repository(self):
        """Test repositories search with GQL."""
        result = await find_type_tool({
            "type": "repository",
            "gql": "name ~ \"archive\"",
            "max_results": 3
        })
        
        print("\n--- FIND REPOSITORY RESULT ---")
        print(result[0].text)
        print("--- END ---\n")
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "error" not in result[0].text.lower(), f"Error found in response: {result[0].text}"
        assert "Found" in result[0].text or "No repositories found" in result[0].text
        
        # Assert max_results is respected - count actual result entries
        if "Found" in result[0].text and "No repositories found" not in result[0].text:
            # Count the number of "• **" entries which indicate individual results
            result_count = result[0].text.count("• **")
            assert result_count <= 3, f"Expected max 3 results, got {result_count}"


class TestFindCitationTool:
    """Test find_type_tool functionality for citation with real API."""
    
    @pytest.mark.asyncio
    async def test_find_citation(self):
        """Test citations search with GQL."""
        result = await find_type_tool({
            "type": "citation",
            "gql": "page ~ \"1624\"",
            "max_results": 3
        })
        
        print("\n--- FIND CITATION RESULT ---")
        print(result[0].text)
        print("--- END ---\n")
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "error" not in result[0].text.lower(), f"Error found in response: {result[0].text}"
        assert "Found" in result[0].text or "No citations found" in result[0].text
        
        # Assert max_results is respected - count actual result entries
        if "Found" in result[0].text and "No citations found" not in result[0].text:
            # Count the number of "• **" entries which indicate individual results
            result_count = result[0].text.count("• **")
            assert result_count <= 3, f"Expected max 3 results, got {result_count}"


class TestFindMediaTool:
    """Test find_type_tool functionality for media with real API."""
    
    @pytest.mark.asyncio
    async def test_find_media(self):
        """Test media search with GQL."""
        result = await find_type_tool({
            "type": "media",
            "gql": "desc ~ \"pietrala\"",
            "max_results": 3
        })
        
        print("\n--- FIND MEDIA RESULT ---")
        print(result[0].text)
        print("--- END ---\n")
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "error" not in result[0].text.lower(), f"Error found in response: {result[0].text}"
        assert "Found" in result[0].text or "No media files found" in result[0].text
        
        # Assert max_results is respected - count actual result entries
        if "Found" in result[0].text and "No media files found" not in result[0].text:
            # Count the number of "• **" entries which indicate individual results
            result_count = result[0].text.count("• **")
            assert result_count <= 3, f"Expected max 3 results, got {result_count}"


class TestFindNoteTool:
    """Test find_type_tool functionality for note with real API."""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Note GQL search not supported by Gramps Web API despite documentation")
    async def test_find_note(self):
        """Test notes search with GQL.
        
        NOTE: Skipped because the Gramps Web API notes endpoint
        does not properly support GQL queries, contrary to the documentation.
        The API returns "Server error" when attempting note searches with GQL.
        """
        result = await find_type_tool({
            "type": "note",
            "gql": "gramps_id ~ \"N0001\"",
            "max_results": 3
        })
        
        print("\n--- FIND NOTE RESULT ---")
        print(result[0].text)
        print("--- END ---\n")
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "error" not in result[0].text.lower(), f"Error found in response: {result[0].text}"
        assert "Found" in result[0].text or "No notes found" in result[0].text
        
        # Assert max_results is respected - count actual result entries
        if "Found" in result[0].text and "No notes found" not in result[0].text:
            # Count the number of "• **" entries which indicate individual results
            result_count = result[0].text.count("• **")
            assert result_count <= 3, f"Expected max 3 results, got {result_count}"


class TestFindAnythingTool:
    """Test find_anything_tool functionality with real API."""
    
    @pytest.mark.asyncio
    async def test_find_anything(self):
        """Test search across all object types with query."""
        result = await find_anything_tool({
            "query": "pietrala",
            "max_results": 3
        })
        
        print("\n--- FIND ANYTHING RESULT ---")
        print(result[0].text)
        print("--- END ---\n")
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "error" not in result[0].text.lower(), f"Error found in response: {result[0].text}"
        assert "Found" in result[0].text and "records matching" in result[0].text
        
        # Assert max_results is respected - count actual result entries
        if "Found" in result[0].text and "No records found" not in result[0].text:
            # Count the number of "• **" entries which indicate individual results
            result_count = result[0].text.count("• **")
            assert result_count <= 3, f"Expected max 3 results, got {result_count}"

