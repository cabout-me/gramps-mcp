"""
Pydantic models for living status operations.

API calls supported in this category:
- GET_LIVING: Get whether or not a person is living
- GET_LIVING_DATES: Get estimated birth and death dates for a person
"""

from typing import Optional

from pydantic import BaseModel, Field


class LivingParams(BaseModel):
    """
    Parameters for living status operations (both status check and date estimation).
    """

    handle: str = Field(
        ..., min_length=1, description="The handle of the person to evaluate"
    )
    average_generation_gap: Optional[int] = Field(
        None, ge=1, description="Average number of years between generations"
    )
    max_age_probably_alive: Optional[int] = Field(
        None,
        ge=1,
        description="Maximum possible age in years someone could be considered alive",
    )
    max_sibling_age_difference: Optional[int] = Field(
        None,
        ge=0,
        description=(
            "Maximum possible age difference in years between youngest and oldest "
            "sibling"
        ),
    )
