"""
Pydantic models for relationship-related operations.

API calls supported in this category:
- GET_RELATION: Get description of most direct relationship between two people
- GET_RELATIONS_ALL: Get descriptions for all possible relationships between two people
"""

from typing import Optional

from pydantic import BaseModel, Field


class RelationParams(BaseModel):
    """Parameters for getting relationships between two people."""

    handle1: str = Field(
        ..., min_length=1, description="The handle of the first person"
    )
    handle2: str = Field(
        ..., min_length=1, description="The handle of the second person"
    )
    depth: Optional[int] = Field(
        None, ge=1, description="Depth for the search, default is 15 generations"
    )
