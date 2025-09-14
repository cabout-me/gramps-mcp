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
Pydantic models for relationship-related operations.

API calls supported in this category:
- GET_RELATION: Get description of most direct relationship between two people
- GET_RELATIONS_ALL: Get descriptions for all possible relationships between two people
"""

from typing import Optional

from pydantic import BaseModel, Field


class RelationParams(BaseModel):
    """Parameters for getting relationships between two people."""

    handle1: str = Field(
        ..., min_length=1, description="The handle of the first person"
    )
    handle2: str = Field(
        ..., min_length=1, description="The handle of the second person"
    )
    depth: Optional[int] = Field(
        None, ge=1, description="Depth for the search, default is 15 generations"
    )
