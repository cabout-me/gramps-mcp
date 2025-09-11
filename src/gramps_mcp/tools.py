"""
MCP tool implementations for genealogy operations.

This module provides a unified interface to all 23 genealogy tools, now
organized in modular sub-packages for better maintainability and scalability.
"""

# Import all tools from the modular structure
from .tools import (
    create_citation_tool,
    create_event_tool,
    create_family_tool,
    create_media_tool,
    create_note_tool,
    # Data Management Tools
    create_person_tool,
    create_place_tool,
    create_repository_tool,
    create_source_tool,
    find_anything_tool,
    find_citation_tool,
    find_event_tool,
    find_family_tool,
    find_media_tool,
    # Search & Discovery Tools
    find_person_tool,
    find_place_tool,
    find_repository_tool,
    find_source_tool,
    get_ancestors_tool,
    get_descendants_tool,
    get_family_tool,
    get_person_tool,
    get_recent_changes_tool,
    # Analysis Tools
    get_tree_info_tool,
)

# Export all tools for external use
__all__ = [
    # Search & Discovery Tools
    "find_person_tool",
    "find_family_tool",
    "find_event_tool",
    "find_place_tool",
    "find_source_tool",
    "find_repository_tool",
    "find_citation_tool",
    "find_media_tool",
    "find_anything_tool",
    "get_person_tool",
    "get_family_tool",
    # Data Management Tools
    "create_person_tool",
    "create_family_tool",
    "create_event_tool",
    "create_place_tool",
    "create_source_tool",
    "create_citation_tool",
    "create_note_tool",
    "create_media_tool",
    "create_repository_tool",
    # Analysis Tools
    "get_tree_info_tool",
    "get_descendants_tool",
    "get_ancestors_tool",
    "get_recent_changes_tool",
]
