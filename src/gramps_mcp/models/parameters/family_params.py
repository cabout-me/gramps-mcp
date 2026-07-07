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

from typing import Any, List, Optional

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

    def to_api_payload(self, **kwargs: Any) -> dict[str, Any]:
        """Serialize for the Gramps Web API, translating ``child_handles``
        (a user-friendly list of handle strings) into ``child_ref_list``
        (a list of ``{"ref": handle}`` dicts) that the API expects.

        ``model_dump`` keeps ``child_handles`` as ``List[str]`` so the model
        can be re-validated or inspected without losing information. The
        Gramps Web REST API does not recognise ``child_handles``; this method
        performs the translation and is what the API client should call when
        building an HTTP request body.
        """
        data = super().model_dump(**kwargs)
        # Translate ``child_handles`` (List[str]) into the ``child_ref_list``
        # (List[{"ref": handle}]) format the Gramps Web API expects. Treat
        # ``None`` and ``[]`` identically: omit ``child_ref_list`` from the
        # payload so existing children are preserved on a PUT, and drop the
        # user-facing ``child_handles`` key so the payload only carries the
        # field the API understands.
        child_handles = data.get("child_handles")
        if child_handles:
            data["child_ref_list"] = [{"ref": h} for h in child_handles]
        data.pop("child_handles", None)
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
