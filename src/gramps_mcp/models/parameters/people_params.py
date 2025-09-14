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
Pydantic models for people-related operations.

API calls supported in this category:
- GET_PEOPLE: Get information about multiple people
- POST_PEOPLE: Add a new person to the database
- GET_PERSON: Get information about a specific person
- PUT_PERSON: Update the person
- DELETE_PERSON: Delete the person
- GET_PERSON_TIMELINE: Get the timeline for a specific person
- GET_PERSON_DNA_MATCHES: Get DNA matches for a specific person
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .base_params import BaseDataModel


class EventReference(BaseModel):
    """Model for event references in a person's event_ref_list."""

    ref: str = Field(..., description="The handle of the event referenced")
    role: str = Field(..., description="Role of the person in the event")


class PersonData(BaseDataModel):
    """Model for creating or updating a person in Gramps API."""

    primary_name: Dict[str, Any] = Field(
        ..., description="Person's primary name object with first_name and surname_list"
    )
    gender: int = Field(
        ..., ge=0, le=2, description="Gender (0=Female, 1=Male, 2=Unknown)"
    )
    event_ref_list: Optional[List[EventReference]] = Field(
        None, description="List of references to events the person participated in"
    )
    family_list: Optional[List[str]] = Field(
        None, description="List of handles for families the person was a parent of"
    )
    parent_family_list: Optional[List[str]] = Field(
        None, description="List of handles for families of the person's parents"
    )
    urls: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of URLs associated with the person"
    )


class PersonTimelineParams(BaseModel):
    """Parameters for getting a person's timeline from Gramps API."""

    dates: Optional[str] = Field(
        None,
        description=(
            "Date range to bound the timeline (e.g., -y/m/d, y/m/d-y/m/d, y/m/d-)"
        ),
    )
    first: Optional[bool] = Field(
        None, description="Discard events dated prior to the first event for the person"
    )
    last: Optional[bool] = Field(
        None, description="Discard events dated after the last event for the person"
    )
    ancestors: Optional[int] = Field(
        None, ge=0, description="Number of generations of ancestors to consider"
    )
    offspring: Optional[int] = Field(
        None, ge=0, description="Number of generations of offspring to consider"
    )
    events: Optional[str] = Field(
        None, description="Comma delimited list of specific events to include"
    )
    event_classes: Optional[str] = Field(
        None, description="Comma delimited list of event classes to include"
    )
    relatives: Optional[str] = Field(
        None, description="Comma delimited list of relationship types to consider"
    )
    relative_events: Optional[str] = Field(
        None, description="Comma delimited list of events for relatives"
    )
    relative_event_classes: Optional[str] = Field(
        None, description="Comma delimited list of event classes for relatives"
    )
    ratings: Optional[bool] = Field(
        None, description="Include citation count and highest confidence score"
    )
    precision: Optional[int] = Field(
        None,
        ge=1,
        le=3,
        description="Number of significant levels for date representation",
    )
    discard_empty: Optional[bool] = Field(None, description="Discard undated events")
    omit_anchor: Optional[bool] = Field(
        None, description="Omit person info for events pertaining to that person"
    )
    page: Optional[int] = Field(None, ge=0, description="Page number for pagination")
    pagesize: Optional[int] = Field(None, ge=1, description="Number of items per page")


class PersonDnaMatchesParams(BaseModel):
    """Parameters for getting DNA matches for a person from Gramps API."""

    raw: Optional[bool] = Field(None, description="Include raw data for the matches")
