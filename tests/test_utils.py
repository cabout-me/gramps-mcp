"""
Tests for utility functions.
"""

import pytest
from dotenv import load_dotenv

from src.gramps_mcp.client import GrampsWebAPIClient
from src.gramps_mcp.config import get_settings
from src.gramps_mcp.utils import (
    format_note_preview,
    get_gramps_id_from_handle,
    html_to_markdown,
)

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

class TestFormatNotePreview:
    """Test the short note preview used in person and family details."""

    def test_styled_text_dict(self):
        """Gramps Web returns note text as a StyledText dict."""
        note = {"text": {"_class": "StyledText", "string": "Short note", "tags": []}}
        assert format_note_preview(note) == "Short note"

    def test_styled_text_dict_truncated(self):
        """Long StyledText notes are cut to the limit with an ellipsis."""
        note = {"text": {"string": "x" * 60, "tags": []}}
        assert format_note_preview(note) == "x" * 50 + "..."

    def test_plain_string(self):
        """A plain string text is still handled."""
        assert format_note_preview({"text": "plain"}) == "plain"

    def test_missing_text(self):
        """A note without text gives an empty preview."""
        assert format_note_preview({}) == ""

    def test_custom_limit(self):
        """The preview length can be changed."""
        note = {"text": {"string": "abcdef"}}
        assert format_note_preview(note, limit=3) == "abc..."
