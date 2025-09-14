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
