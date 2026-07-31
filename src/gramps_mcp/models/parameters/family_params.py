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
        None, description="List of child person handles"
    )
    # Internal/API shape. Callers should use `child_handles`; model_dump() below
    # converts those into this ChildRef list, which is what the Gramps API
    # actually persists. Declared as a field (not only built inside model_dump)
    # so the FastMCP validate -> model_dump -> re-validate round-trip preserves
    # it instead of dropping it as an unknown key (which silently lost every
    # child).
    child_ref_list: Optional[List[dict]] = Field(
        None, description="ChildRef objects (built from child_handles; advanced use)"
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

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Convert child_handles into the ChildRef list the Gramps API expects.

        The API stores children as ``child_ref_list`` entries shaped like
        ``{"_class": "ChildRef", "ref": <handle>, "frel": "Birth",
        "mrel": "Birth"}`` — NOT as a bare ``child_handles`` list. Sending
        ``child_handles`` makes the API silently ignore it: the family saves
        but with no children. Here we translate handles into ChildRef objects
        (deduped against any explicit ``child_ref_list``) and drop the
        ``child_handles`` key. grampsweb maintains the reciprocal
        ``parent_family_list`` on each child automatically.
        """
        data = super().model_dump(**kwargs)
        handles = data.pop("child_handles", None)
        if handles:
            child_refs = data.get("child_ref_list") or []
            seen = {r.get("ref") for r in child_refs if isinstance(r, dict)}
            for handle in handles:
                if handle not in seen:
                    child_refs.append(
                        {
                            "_class": "ChildRef",
                            "ref": handle,
                            "frel": "Birth",
                            "mrel": "Birth",
                        }
                    )
                    seen.add(handle)
            data["child_ref_list"] = child_refs
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
