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

This module exports all 39 genealogy tools organized by category:
- Search & Discovery Tools (3)
- Data Management Tools (9 create + 10 delete + 4 tag/media + 2 upload = 25)
- Analysis Tools (11)
"""

# Analysis Tools (11 tools)
from .analysis import (
    get_ancestors_tool,
    get_descendants_tool,
    get_event_span_tool,
    get_facts_tool,
    get_families_timeline_tool,
    get_living_tool,
    get_people_timeline_tool,
    get_recent_changes_tool,
    get_relations_all_tool,
    get_relations_tool,
    get_tree_info_tool,
    get_types_tool,
)

# Data Management Tools (25 tools)
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
    create_tag_tool,
    delete_citation_tool,
    delete_event_tool,
    delete_family_tool,
    delete_media_tool,
    delete_note_tool,
    delete_person_tool,
    delete_place_tool,
    delete_repository_tool,
    delete_source_tool,
    delete_tag_tool,
    find_tags_tool,
    get_media_file_tool,
    update_media_file_tool,
    upload_media_file_tool,
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
    # Data Management Tools - Create
    "create_person_tool",
    "create_family_tool",
    "create_event_tool",
    "create_place_tool",
    "create_source_tool",
    "create_citation_tool",
    "create_note_tool",
    "create_media_tool",
    "create_repository_tool",
    "create_tag_tool",
    # Data Management Tools - Delete
    "delete_person_tool",
    "delete_family_tool",
    "delete_event_tool",
    "delete_note_tool",
    "delete_citation_tool",
    "delete_source_tool",
    "delete_place_tool",
    "delete_repository_tool",
    "delete_media_tool",
    "delete_tag_tool",
    # Data Management Tools - Tags & Media
    "find_tags_tool",
    "get_media_file_tool",
    "upload_media_file_tool",
    "update_media_file_tool",
    # Analysis Tools
    "get_tree_info_tool",
    "get_descendants_tool",
    "get_ancestors_tool",
    "get_recent_changes_tool",
    "get_relations_tool",
    "get_relations_all_tool",
    "get_living_tool",
    "get_facts_tool",
    "get_people_timeline_tool",
    "get_families_timeline_tool",
    "get_event_span_tool",
    "get_types_tool",
]
