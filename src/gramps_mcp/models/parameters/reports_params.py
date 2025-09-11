"""
Parameters for reports endpoints.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ReportGetParams(BaseModel):
    """
    Parameters for getting information about a specific report.

    Args:
        report_id (str): ID of the report to get information for
        include_help (Optional[bool]): Whether to include report options help

    Returns:
        Dict[str, Any]: Report information
    """

    include_help: Optional[bool] = Field(
        None, description="Whether to include report options help"
    )


class ReportFileParams(BaseModel):
    """
    Parameters for getting a specific report file.

    Args:
        report_id (str): ID of the report to get
        options (Optional[str]): Report options in JSON format

    Returns:
        Any: Report file content
    """

    options: Optional[str] = Field(None, description="Report options in JSON format")
