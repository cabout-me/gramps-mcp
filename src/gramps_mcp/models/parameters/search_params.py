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
Pydantic models for search-related operations.

API calls supported in this category:
- GET_SEARCH: Perform a full-text search on multiple objects
"""

from typing import Optional

from pydantic import BaseModel, Field


class SearchParams(BaseModel):
    """
    Parameters for performing a full-text search on multiple objects.

    Used by GET /search endpoint.
    """

    query: str = Field(..., description="The search string")
    page: Optional[int] = Field(
        None,
        description=(
            "The page number representing the subset of search results to be returned"
        ),
    )
    pagesize: Optional[int] = Field(
        None, description="The number of search results that constitute a page"
    )
    type: Optional[str] = Field(
        None, description="A comma delimited list of object types to include"
    )
    sort: Optional[str] = Field(
        None, description="A comma delimited list of keys to sort the result set by"
    )
    profile: Optional[str] = Field(
        None,
        description=(
            "Enables the return of summarized information about a person, family, "
            "or event"
        ),
    )
    semantic: Optional[bool] = Field(
        None,
        description=(
            "Indicates whether semantic search should be used rather than "
            "full-text search"
        ),
    )
