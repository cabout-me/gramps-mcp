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

"""Pydantic models for note-related operations.

API calls supported in this category:
- GET_NOTES: Get information about multiple notes
- POST_NOTES: Add a new note to the database
- GET_NOTE: Get information about a specific note
- PUT_NOTE: Update the note
- DELETE_NOTE: Delete the note
"""

from typing import Any

from pydantic import BaseModel, Field

from .base_params import BaseGetMultipleParams, BaseGetSingleParams


class NotesParams(BaseGetMultipleParams):
    """Parameters for getting information about multiple notes."""

    formats: str | None = Field(
        None,
        description="Comma delimited list of formats to apply (html)",
    )
    format_options: str | None = Field(
        None,
        description="JSON dictionary of options for note formatters",
    )


class NoteParams(BaseGetSingleParams):
    """Parameters for getting information about a specific note."""

    formats: str | None = Field(
        None,
        description="Comma delimited list of formats to apply (html)",
    )
    format_options: str | None = Field(
        None,
        description="JSON dictionary of options for note formatters",
    )


class NoteSaveParams(BaseModel):
    """Parameters for creating or updating a note."""

    handle: str | None = Field(
        None,
        description="Note's handle (for updates; omit for new note)",
    )
    text: str = Field(..., description="Note text content")
    type: str = Field(..., description="The type of note")

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Convert to API format with StyledText structure."""
        data = super().model_dump(**kwargs)
        # Transform text string to StyledText format expected by API
        if "text" in data and isinstance(data["text"], str):
            data["text"] = {
                "_class": "StyledText",
                "string": data["text"],
            }
        return data
