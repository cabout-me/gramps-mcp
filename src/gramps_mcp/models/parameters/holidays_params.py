"""
Parameter models for holidays API endpoints.
"""

from pydantic import BaseModel, Field


class HolidaysParams(BaseModel):
    """
    Parameters for getting holidays for a specific date and country.

    Args:
        country (str): The country name.
        year (int): The year.
        month (int): The month (1-12).
        day (int): The day of the month.
    """

    country: str = Field(..., description="The country name")
    year: int = Field(..., description="The year")
    month: int = Field(..., ge=1, le=12, description="The month (1-12)")
    day: int = Field(..., ge=1, le=31, description="The day of the month")
