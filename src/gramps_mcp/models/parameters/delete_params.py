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
Delete parameters for Gramps MCP tools.

Supported API Calls:
- DELETE_PERSON: Delete a person
- DELETE_FAMILY: Delete a family
"""

from pydantic import BaseModel, Field


class DeleteParams(BaseModel):
    """Parameters for deleting an entity."""

    handle: str = Field(..., description="Handle of the entity to delete")
