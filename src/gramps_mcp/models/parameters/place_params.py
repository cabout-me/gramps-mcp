"""
Pydantic models for place-related operations.

API calls supported in this category:
- GET_PLACES: Get information about multiple places
- POST_PLACES: Add a new place to the database
- GET_PLACE: Get information about a specific place
- PUT_PLACE: Update the place
- DELETE_PLACE: Delete the place
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from .base_params import BaseGetMultipleParams, BaseGetSingleParams


class PlaceSearchParams(BaseGetMultipleParams):
    """Parameters for searching places."""

    pass


class PlaceDetailsParams(BaseGetSingleParams):
    """Parameters for getting specific place details."""

    pass


class PlaceSaveParams(BaseModel):
    """Parameters for creating or updating a place."""

    handle: Optional[str] = Field(
        None, min_length=8, description="Place handle (for updates; omit for new place)"
    )
    gramps_id: Optional[str] = Field(
        None, description="Alternate user managed identifier"
    )
    name: Optional[dict] = Field(
        None, description="Place name object with 'value' field"
    )
    code: Optional[str] = Field(None, description="Place code")
    alt_loc: Optional[List[dict]] = Field(None, description="Alternative locations")
    place_type: str = Field(..., description="Place type")
    placeref_list: Optional[List[dict]] = Field(
        None, description="List of place references"
    )
    alt_names: Optional[List[str]] = Field(None, description="Alternative names")
    lat: Optional[str] = Field(None, description="Latitude coordinate")
    long: Optional[str] = Field(None, description="Longitude coordinate")
    urls: Optional[List[dict]] = Field(None, description="Associated URLs")
    media_list: Optional[List[str]] = Field(None, description="List of media handles")
    citation_list: Optional[List[str]] = Field(
        None, description="List of citation handles"
    )
    note_list: Optional[List[str]] = Field(None, description="List of note handles")
    tag_list: Optional[List[str]] = Field(None, description="List of tag handles")
    private: Optional[bool] = Field(None, description="Mark as private")
