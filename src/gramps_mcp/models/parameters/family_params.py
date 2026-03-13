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
Pydantic models for family-related operations.

API calls supported in this category:
- GET_FAMILIES: Get information about multiple families
- POST_FAMILIES: Add a new family to the database
- GET_FAMILY: Get information about a specific family
- PUT_FAMILY: Update the family
- DELETE_FAMILY: Delete the family
- GET_FAMILY_TIMELINE: Get the timeline for all the people in a specific family
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_serializer


class ChildReference(BaseModel):
    """Model for child references in a family's child_ref_list."""

    ref: str = Field(..., description="The handle of the child person")
    frel: str = Field(default="Birth", description="Father relationship type")
    mrel: str = Field(default="Birth", description="Mother relationship type")
    citation_list: List[str] = Field(default_factory=list)
    note_list: List[str] = Field(default_factory=list)
    private: bool = Field(default=False)


class FamilySaveParams(BaseModel):
    """Parameters for creating or updating a family."""

    handle: Optional[str] = Field(
        None, description="Family's handle (for updates; omit for new family)"
    )
    father_handle: Optional[str] = Field(None, description="Father's handle")
    mother_handle: Optional[str] = Field(None, description="Mother's handle")
    child_handles: Optional[List[str]] = Field(
        None,
        description="List of child handles (convenience field, converted to child_ref_list)",
    )
    child_ref_list: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="List of child references with relationship details",
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

    @model_serializer
    def serialize_model(self) -> Dict[str, Any]:
        """
        Custom serializer that converts child_handles to child_ref_list format.

        The Gramps Web API expects child_ref_list with full reference objects,
        not a simple list of handles. This serializer performs that conversion.
        """
        data = {}

        # Add standard fields
        if self.handle is not None:
            data["handle"] = self.handle
        if self.father_handle is not None:
            data["father_handle"] = self.father_handle
        if self.mother_handle is not None:
            data["mother_handle"] = self.mother_handle
        if self.event_ref_list is not None:
            data["event_ref_list"] = self.event_ref_list
        if self.note_list is not None:
            data["note_list"] = self.note_list
        if self.urls is not None:
            data["urls"] = self.urls
        if self.media_list is not None:
            data["media_list"] = self.media_list

        # Convert child_handles to child_ref_list if provided
        # Reason: The API expects child_ref_list with full reference objects,
        # but child_handles is more convenient for users to specify
        if self.child_handles is not None:
            child_refs = [
                ChildReference(ref=handle).model_dump()
                for handle in self.child_handles
            ]
            # Merge with any existing child_ref_list
            if self.child_ref_list is not None:
                existing_refs = set(
                    ref.get("ref") for ref in self.child_ref_list if ref.get("ref")
                )
                new_refs = [r for r in child_refs if r["ref"] not in existing_refs]
                data["child_ref_list"] = self.child_ref_list + new_refs
            else:
                data["child_ref_list"] = child_refs
        elif self.child_ref_list is not None:
            data["child_ref_list"] = self.child_ref_list

        return data


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
