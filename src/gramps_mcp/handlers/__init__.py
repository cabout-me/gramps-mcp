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
Handlers for formatting Gramps data entities.

This package contains dedicated handlers for each entity type that convert
raw API data into formatted display strings.
"""

from .citation_handler import format_citation
from .date_handler import format_date
from .event_handler import format_event
from .family_handler import format_family
from .media_handler import format_media
from .note_handler import format_note
from .person_handler import format_person
from .place_handler import format_place
from .repository_handler import format_repository
from .source_handler import format_source

__all__ = [
    "format_person",
    "format_family",
    "format_event",
    "format_place",
    "format_source",
    "format_media",
    "format_date",
    "format_note",
    "format_repository",
    "format_citation",
]
