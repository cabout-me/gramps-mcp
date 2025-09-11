"""
Pydantic models for family-related operations.

API calls supported in this category:
- GET_FAMILIES: Get information about multiple families
- POST_FAMILIES: Add a new family to the database
- GET_FAMILY: Get information about a specific family
- PUT_FAMILY: Update the family
- DELETE_FAMILY: Delete the family
- GET_FAMILY_TIMELINE: Get the timeline for all the people in a specific family
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class FamilySaveParams(BaseModel):
    """Parameters for creating or updating a family."""

    handle: Optional[str] = Field(
        None, description="Family's handle (for updates; omit for new family)"
    )
    father_handle: Optional[str] = Field(None, description="Father's handle")
    mother_handle: Optional[str] = Field(None, description="Mother's handle")
    child_handles: Optional[List[str]] = Field(
        None, description="List of child handles"
    )
    event_ref_list: Optional[List[dict]] = Field(
        None, description="List of event references"
    )
    note_list: Optional[List[str]] = Field(None, description="List of note handles")
    urls: Optional[List[dict]] = Field(
        None, description="List of URLs associated with the family"
    )
    media_list: Optional[List[dict]] = Field(
        None, description="List of media references"
    )


class FamilyTimelineParams(BaseModel):
    """Parameters for getting family timeline information."""

    handle: str = Field(min_length=8, description="The unique identifier for a family")
    dates: Optional[str] = Field(None, description="Date range to bound the timeline")
    events: Optional[str] = Field(
        None, description="Comma delimited list of specific events"
    )
    event_classes: Optional[str] = Field(
        None, description="Comma delimited list of event classes"
    )
    ratings: Optional[bool] = Field(
        None, description="Include citation count and highest confidence score"
    )
    discard_empty: Optional[bool] = Field(None, description="Discard undated events")
    page: Optional[int] = Field(None, ge=0, description="Page number for pagination")
    pagesize: Optional[int] = Field(None, ge=1, description="Number of items per page")
