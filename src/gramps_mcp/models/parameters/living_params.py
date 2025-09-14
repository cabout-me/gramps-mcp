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
