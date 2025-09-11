"""
Timeline parameter models for the Gramps Web API.
"""

from typing import Optional

from pydantic import BaseModel, Field


class PeopleTimelineParams(BaseModel):
    """
    Parameters for getting the timeline for a group of people.

    Args:
        anchor: Handle of a person to anchor the timeline.
        dates: Date range to bound the timeline (formats: -y/m/d, y/m/d-y/m/d, y/m/d-).
        first: Whether events prior to anchor person's first event should be included.
        last: Whether events after anchor person's last event should be included.
        handles: Comma delimited list of handles for specific people.
        events: Comma delimited list of specific events to include.
        event_classes: Comma delimited list of event classes to include.
        ratings: Whether to include citation count and confidence score.
        precision: Number of significant levels for date representation (1-3).
        discard_empty: Whether to discard undated events.
        omit_anchor: Whether to omit anchor person info from their own events.
        page: Page number for pagination.
        pagesize: Number of items per page.
    """

    anchor: Optional[str] = None
    dates: Optional[str] = None
    first: bool = True
    last: bool = True
    handles: Optional[str] = None
    events: Optional[str] = None
    event_classes: Optional[str] = None
    ratings: bool = False
    precision: int = Field(default=1, ge=1, le=3)
    discard_empty: bool = True
    omit_anchor: bool = True
    page: int = Field(default=0, ge=0)
    pagesize: int = Field(default=20, gt=0)


class FamiliesTimelineParams(BaseModel):
    """
    Parameters for getting the timeline for all people in a group of families.

    Args:
        handles: Comma delimited list of handles for specific families.
        dates: Date range to bound the timeline (formats: -y/m/d, y/m/d-y/m/d, y/m/d-).
        events: Comma delimited list of specific events to include.
        event_classes: Comma delimited list of event classes to include.
        ratings: Whether to include citation count and confidence score.
        discard_empty: Whether to discard undated events.
        page: Page number for pagination.
        pagesize: Number of items per page.
    """

    handles: Optional[str] = None
    dates: Optional[str] = None
    events: Optional[str] = None
    event_classes: Optional[str] = None
    ratings: bool = False
    discard_empty: bool = True
    page: int = Field(default=0, ge=0)
    pagesize: int = Field(default=20, gt=0)
