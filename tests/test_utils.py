"""
Tests for utility functions.
"""

import pytest
from dotenv import load_dotenv

from src.gramps_mcp.client import GrampsWebAPIClient
from src.gramps_mcp.config import get_settings
from src.gramps_mcp.utils import get_gramps_id_from_handle, html_to_markdown

# Load environment variables from .env file
load_dotenv()


class TestHTMLToMarkdown:
    """Test HTML to Markdown conversion utility."""
    
    def test_basic_html_conversion(self):
        """Test basic HTML elements conversion."""
        html = "<h1>Title</h1><p>This is a paragraph.</p>"
        expected = "# Title\n\nThis is a paragraph."
        assert html_to_markdown(html).strip() == expected


class TestGetGrampsIdFromHandle:
    """Test get_gramps_id_from_handle utility function."""

    @pytest.mark.asyncio
    async def test_unknown_object_type_returns_handle(self):
        """Test that unknown object types return the original handle."""
        
        settings = get_settings()
        client = GrampsWebAPIClient()
        
        try:
            result = await get_gramps_id_from_handle(
                client, "unknown_type", "test_handle", settings.gramps_tree_id
            )
            
            # Should return the original handle for unknown types
            assert result == "test_handle"
        
        finally:
            await client.close()