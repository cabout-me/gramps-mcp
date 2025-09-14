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
Pydantic models for event-related operations.

API calls supported in this category:
- GET_EVENTS: Get information about multiple events
- POST_EVENTS: Add a new event to the database
- GET_EVENT: Get information about a specific event
- PUT_EVENT: Update the event
- DELETE_EVENT: Delete the event
- GET_EVENT_SPAN: Get elapsed time span between two events
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .base_params import BaseGetMultipleParams


class EventSearchParams(BaseGetMultipleParams):
    """Parameters for searching multiple events."""

    dates: Optional[str] = Field(
        None, description="Date filter (y/m/d, -y/m/d, y/m/d-y/m/d, y/m/d-)"
    )


class EventSaveParams(BaseModel):
    """Parameters for creating or updating an event."""

    handle: Optional[str] = Field(
        None, description="Event's handle (for updates; omit for new event)"
    )
    type: str = Field(description="Event type (Birth, Death, Marriage, etc.)")
    date: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Event date object with dateval array [day, month, year, False], "
            "quality (0=regular, 1=estimated, 2=calculated), and modifier "
            "(0=regular, 1=before, 2=after, 3=about, 4=range, 5=span, "
            "6=textonly, 7=from, 8=to)"
        ),
    )
    description: Optional[str] = Field(None, description="Event description")
    place: Optional[str] = Field(None, description="Place handle where event occurred")
    citation_list: List[str] = Field(..., description="List of citation handles")
    note_list: Optional[List[str]] = Field(None, description="List of note handles")


class EventSpanParams(BaseModel):
    """Parameters for getting elapsed time span between two events."""

    handle1: str = Field(description="The unique identifier for the first event")
    handle2: str = Field(description="The unique identifier for the second event")
    as_age: Optional[bool] = Field(None, description="Return result as an age")
    precision: Optional[int] = Field(
        None, ge=1, le=3, description="Number of significant levels (1-3)"
    )
