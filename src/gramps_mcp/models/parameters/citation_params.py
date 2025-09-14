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
Pydantic models for citation-related operations.

API calls supported in this category:
- GET_CITATIONS: Get information about multiple citations
- POST_CITATIONS: Add a new citation to the database
- GET_CITATION: Get information about a specific citation
- PUT_CITATION: Update the citation
- DELETE_CITATION: Delete the citation
"""

from typing import Any, Dict, Optional

from pydantic import Field

from .base_params import BaseDataModel, BaseGetMultipleParams


class GetCitationsParams(BaseGetMultipleParams):
    """Parameters for GET /citations endpoint."""

    dates: Optional[str] = Field(
        None, description="A date filter that operates on the citation date."
    )


class CitationData(BaseDataModel):
    """Model for creating or updating a citation via POST/PUT endpoints."""

    date: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Date object with dateval array [day, month, year, False], "
            "quality (0=regular, 1=estimated, 2=calculated), and modifier "
            "(0=regular, 1=before, 2=after, 3=about, 4=range, 5=span, "
            "6=textonly, 7=from, 8=to)"
        ),
    )
    page: Optional[str] = Field(None, description="Page or location within the source")
    source_handle: str = Field(..., description="Handle of the source being cited")
