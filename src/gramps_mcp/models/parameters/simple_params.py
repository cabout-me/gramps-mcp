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
Simplified parameter models for reduced token usage.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """All searchable entity types in Gramps."""

    PERSON = "person"
    FAMILY = "family"
    EVENT = "event"
    PLACE = "place"
    SOURCE = "source"
    CITATION = "citation"
    MEDIA = "media"
    REPOSITORY = "repository"
    NOTE = "note"


class GetEntityType(str, Enum):
    """Entity types that support detailed get operations."""

    PERSON = "person"
    FAMILY = "family"


class SimpleFindParams(BaseModel):
    """Simplified parameters for type-based search."""

    type: EntityType = Field(description="Entity type to search")
    gql: str = Field(description="Gramps Query Language filter")
    max_results: int = Field(default=20, description="Maximum results to return")


class SimpleSearchParams(BaseModel):
    """Simplified parameters for full-text search."""

    query: str = Field(description="Plain text search query")
    max_results: int = Field(default=20, description="Maximum results to return")


class SimpleGetParams(BaseModel):
    """Simplified parameters for getting entity details."""

    type: GetEntityType = Field(description="Entity type (person or family)")
    handle: Optional[str] = Field(default=None, description="Entity handle")
    gramps_id: Optional[str] = Field(
        default=None, description="Gramps ID (e.g., I0001 or F0001)"
    )
