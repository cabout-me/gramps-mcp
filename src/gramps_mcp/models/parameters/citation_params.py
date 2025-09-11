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
