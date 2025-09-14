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
