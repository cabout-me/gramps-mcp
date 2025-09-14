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
Pydantic models for parser-related operations.

API calls supported in this category:
- POST_PARSE_DNA_MATCH: Parse a DNA match file and return structured data
"""

from pydantic import BaseModel, Field


class DnaMatchParseParams(BaseModel):
    """Parameters for parsing DNA match data from Gramps API."""

    string: str = Field(..., description="The raw DNA match data to parse")
