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
