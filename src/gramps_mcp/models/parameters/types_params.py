"""
Parameters for types endpoints.
"""

from pydantic import BaseModel, Field


class TypesParams(BaseModel):
    """
    Parameters for getting type information (values or mapping) for a specific datatype.

    Used for both:
    - GET /types/default/{datatype} - Get values for the datatype
    - GET /types/default/{datatype}/map - Get mapping for the datatype
    """

    datatype: str = Field(..., description="The datatype to get information for")
