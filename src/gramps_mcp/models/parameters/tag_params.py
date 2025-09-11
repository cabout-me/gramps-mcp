"""
Pydantic models for tag-related operations.

API calls supported in this category:
- GET_TAGS: Get information about multiple tags
- POST_TAGS: Add a new tag to the database
- GET_TAG: Get information about a specific tag
- PUT_TAG: Update the tag
- DELETE_TAG: Delete the tag
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class TagSearchParams(BaseModel):
    """Parameters for searching tags."""

    page: Optional[int] = Field(None, description="Page number for pagination", ge=0)
    pagesize: Optional[int] = Field(
        None, description="Number of results per page", ge=1, le=100
    )
    sort: Optional[List[str]] = Field(None, description="Sort order for results")


class TagSaveParams(BaseModel):
    """Parameters for creating or updating a tag."""

    handle: Optional[str] = Field(
        None, description="Tag's handle (for updates; omit for new tag)"
    )
    name: str = Field(description="Tag name", min_length=1)
    color: Optional[str] = Field(None, description="Tag color")
    priority: Optional[int] = Field(None, description="Tag priority")
    change: Optional[str] = Field(None, description="Change timestamp")
