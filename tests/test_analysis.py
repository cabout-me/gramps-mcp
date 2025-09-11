"""
Integration tests for analysis tools using real Gramps Web API.

Tests get_descendants, get_ancestors, and get_recent_changes tools.
These tests require a working Gramps Web API instance with valid credentials.
"""

import pytest
from dotenv import load_dotenv
from mcp.types import TextContent

from src.gramps_mcp.tools.analysis import (
    get_ancestors_tool,
    get_descendants_tool,
    get_recent_changes_tool,
    get_tree_info_tool,
)

# Load environment variables from .env file
load_dotenv()

# Test constants
TEST_PAGESIZE = 3
TEST_MAX_GENERATIONS = 2
INVALID_GRAMPS_ID = "INVALID99999"


def extract_handle_from_search(search_text: str):
    """Extract handle from search result text."""
    import re
    
    # Format: Name (gender) - gramps_id - [handle]
    handle_match = re.search(r"\[([a-f0-9]+)\]", search_text)
    
    if handle_match:
        return handle_match.group(1)
    return None


def extract_gramps_id_from_search(search_text: str):
    """Extract gramps_id from search result text."""
    import re
    
    # Format: Name (gender) - gramps_id - [handle]
    id_match = re.search(r"\([FM]\) - ([^-]+) - \[", search_text)
    
    if id_match:
        return id_match.group(1).strip()
    return None


class TestGetDescendantsTool:
    """Test get_descendants_tool functionality."""

    @pytest.mark.asyncio
    async def test_get_descendants_real_api(self):
        """Test get_descendants_tool with real API."""

        # First search for a person with children to get a valid handle for descendants test
        from src.gramps_mcp.tools.search_basic import find_person_tool

        search_result = await find_person_tool({"query": "*", "pagesize": TEST_PAGESIZE})

        # If we found a person, extract their gramps_id and use it directly
        if "[" in search_result[0].text and "]" in search_result[0].text:
            gramps_id = extract_gramps_id_from_search(search_result[0].text)

            if gramps_id:
                # Test with explicit max_generations
                result_explicit = await get_descendants_tool(
                    {"gramps_id": gramps_id, "max_generations": TEST_MAX_GENERATIONS}
                )
                
                # Test with default max_generations (should be 5)
                result_default = await get_descendants_tool({"gramps_id": gramps_id})

                # Test explicit result
                assert isinstance(result_explicit, list)
                assert len(result_explicit) == 1
                assert isinstance(result_explicit[0], TextContent)

                text_explicit = result_explicit[0].text
                print("\n=== DESCENDANTS TEST OUTPUT (EXPLICIT) ===")
                print(f"Person gramps_id used: {gramps_id}")
                print(f"Max generations: {TEST_MAX_GENERATIONS}")
                print(f"Total lines: {len(text_explicit.split('\n'))}")
                
                # Test default result
                assert isinstance(result_default, list)
                assert len(result_default) == 1
                assert isinstance(result_default[0], TextContent)
                
                text_default = result_default[0].text
                print("\n=== DESCENDANTS TEST OUTPUT (DEFAULT) ===")
                print(f"Person gramps_id used: {gramps_id}")
                print(f"Max generations: DEFAULT (should be 5)")
                print(f"Total lines: {len(text_default.split('\n'))}")
                print("=" * 50)

                # Both should contain actual descendants data
                for text in [text_explicit, text_default]:
                    assert isinstance(text, str)
                    assert len(text) > 0
                    assert len(text.strip()) > 50  # Should be substantial content
                    assert "report generated successfully" not in text.lower()
                    # Report should contain genealogy-related content
                    assert any(
                        keyword in text.lower()
                        for keyword in [
                            "person",
                            "name",
                            "birth",
                            "death",
                            "descendant",
                            "child",
                            "family",
                        ]
                    )
        else:
            # If no people found in a populated tree, this is a test failure
            pytest.fail(
                "No people found for descendants test - tree should be populated"
            )

    @pytest.mark.asyncio
    async def test_get_descendants_invalid_gramps_id(self):
        """Test descendants retrieval with invalid gramps ID."""

        result = await get_descendants_tool({"gramps_id": INVALID_GRAMPS_ID})

        text = result[0].text
        assert "Error:" in text or "No descendants found" in text


class TestGetAncestorsTool:
    """Test get_ancestors_tool functionality."""

    @pytest.mark.asyncio
    async def test_get_ancestors_real_api(self):
        """Test get_ancestors_tool with real API."""

        # Use specific person I0001 for ancestor testing (known to have ancestors)
        gramps_id = "I0001"
        
        # Test with explicit max_generations
        result_explicit = await get_ancestors_tool(
            {"gramps_id": gramps_id, "max_generations": TEST_MAX_GENERATIONS}
        )
        
        # Test with default max_generations (should be 5)
        result_default = await get_ancestors_tool({"gramps_id": gramps_id})

        # Test explicit result
        assert isinstance(result_explicit, list)
        assert len(result_explicit) == 1
        assert isinstance(result_explicit[0], TextContent)

        text_explicit = result_explicit[0].text
        print("\n=== ANCESTORS TEST OUTPUT (EXPLICIT) ===")
        print(f"Person gramps_id used: {gramps_id}")
        print(f"Max generations: {TEST_MAX_GENERATIONS}")
        print(f"Total lines: {len(text_explicit.split('\n'))}")
        
        # Test default result
        assert isinstance(result_default, list)
        assert len(result_default) == 1
        assert isinstance(result_default[0], TextContent)
        
        text_default = result_default[0].text
        print("\n=== ANCESTORS TEST OUTPUT (DEFAULT) ===")
        print(f"Person gramps_id used: {gramps_id}")
        print(f"Max generations: DEFAULT (should be 5)")
        print(f"Total lines: {len(text_default.split('\n'))}")
        print("=" * 50)

        # Both should contain actual ancestors data
        for text in [text_explicit, text_default]:
            assert isinstance(text, str)
            assert len(text) > 0
            assert len(text.strip()) > 50  # Should be substantial content
            assert "report generated successfully" not in text.lower()
            # Report should contain genealogy-related content - check for "Generation" which appears in ancestor reports
            assert "generation" in text.lower()

    @pytest.mark.asyncio
    async def test_get_ancestors_invalid_gramps_id(self):
        """Test ancestors retrieval with invalid gramps ID."""

        result = await get_ancestors_tool({"gramps_id": INVALID_GRAMPS_ID})

        text = result[0].text
        assert "Error:" in text or "No ancestors found" in text


class TestGetRecentChangesTool:
    """Test get_recent_changes_tool functionality."""

    @pytest.mark.asyncio
    async def test_get_recent_changes_real_api(self):
        """Test get_recent_changes_tool with real API."""

        result = await get_recent_changes_tool({"page": 1, "pagesize": 10})

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)

        text = result[0].text
        print("\n=== RECENT CHANGES TEST OUTPUT ===")
        print(f"Result: {text}")
        print("=" * 50)

        assert "recent changes" in text.lower()
        # With populated tree, expect actual recent changes data
        assert "found" in text.lower() and "no recent changes found" not in text.lower()

        # Count the number of transaction entries (each starts with "• **")
        transaction_count = text.count("• **")
        assert 1 <= transaction_count <= 10, f"Expected 1-10 transactions but got {transaction_count}"

        # Should show gramps_id instead of handle
        if "Objects changed:" in text:
            # Gramps IDs follow pattern: Letter + 4 digits (e.g., I0001, F0002, O0506)
            import re

            assert re.search(r"[A-Z]\d{4}", text), (
                "Should show gramps IDs (letter + 4 digits)"
            )


class TestGetTreeInfoTool:
    """Test get_tree_info_tool functionality."""

    @pytest.mark.asyncio
    async def test_get_tree_info_real_api(self):
        """Test get_tree_info_tool with real API."""

        result = await get_tree_info_tool({"include_statistics": True})

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)

        text = result[0].text
        print("\n=== TREE INFO TEST OUTPUT ===")
        print(f"Result: {text}")
        print("=" * 50)

        # Should contain tree information
        assert "Family Tree:" in text
        assert "Tree ID:" in text

        # Should contain statistics (not "Statistics not available")
        assert "Statistics not available" not in text

        # Should contain actual counts
        assert "People:" in text or "people_count" in text.lower()
        
        # Should show media storage in MB format
        assert "MB" in text


# Note: AnalysisClient tests removed as we now use unified GrampsWebAPIClient


