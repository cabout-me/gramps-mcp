# gramps-mcp - AI-Powered Genealogy Research & Management
# Copyright (C) 2025 cabout.me
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Unified interface for all MCP tools.

This module exports all 24 genealogy tools organized by category:
- Search & Discovery Tools (10)
- Data Management Tools (9)
- Analysis Tools (5)
"""

# Search & Discovery Tools (10 tools)
# Analysis Tools (4 tools)
from .analysis import (
    get_ancestors_tool,
    get_descendants_tool,
    get_recent_changes_tool,
    get_tree_info_tool,
)

# Data Management Tools (9 tools)
from .data_management import (
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
from .search_basic import (
    find_anything_tool,
    find_citation_tool,
    find_event_tool,
    find_family_tool,
    find_media_tool,
    find_person_tool,
    find_place_tool,
    find_repository_tool,
    find_source_tool,
)
from .search_details import (
    get_family_tool,
    get_person_tool,
)

# Export all tools for easy import
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
