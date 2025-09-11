"""
Pydantic models for parser-related operations.

API calls supported in this category:
- POST_PARSE_DNA_MATCH: Parse a DNA match file and return structured data
"""

from pydantic import BaseModel, Field


class DnaMatchParseParams(BaseModel):
    """Parameters for parsing DNA match data from Gramps API."""

    string: str = Field(..., description="The raw DNA match data to parse")
