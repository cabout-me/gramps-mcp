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
