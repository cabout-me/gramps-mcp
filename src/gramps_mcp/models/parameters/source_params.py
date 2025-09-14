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
Pydantic models for source-related operations.

API calls supported in this category:
- GET_SOURCES: Get information about multiple sources
- POST_SOURCES: Add a new source to the database
- GET_SOURCE: Get information about a specific source
- PUT_SOURCE: Update the source
- DELETE_SOURCE: Delete the source
"""

from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from .base_params import BaseDataModel, BaseGetMultipleParams, BaseGetSingleParams

# Source-specific constants
SOURCE_EXTEND_CHOICES = [
    "all",
    "media_list",
    "note_list",
    "reporef_list",
    "tag_list",
    "backlinks",
]

SOURCE_SORT_KEYS = [
    "abbrev",
    "author",
    "change",
    "gramps_id",
    "private",
    "pubinfo",
    "title",
]


class SourceSearchParams(BaseGetMultipleParams):
    """
    Parameters for searching sources in the Gramps Web API.

    Used for GET /sources endpoint.
    """

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, v):
        if v is not None:
            # Parse comma-separated sort keys
            sort_keys = [key.strip().lstrip("-") for key in v.split(",")]
            for key in sort_keys:
                if key not in SOURCE_SORT_KEYS:
                    raise ValueError(
                        f"Invalid sort key: {key}. Must be one of {SOURCE_SORT_KEYS}"
                    )
        return v

    @field_validator("extend")
    @classmethod
    def validate_extend(cls, v):
        if v is not None:
            # Convert comma-separated string to list for validation
            extend_list = [choice.strip() for choice in v.split(",")]
            for choice in extend_list:
                if choice not in SOURCE_EXTEND_CHOICES:
                    raise ValueError(
                        f"Invalid extend choice: {choice}. "
                        f"Must be one of {SOURCE_EXTEND_CHOICES}"
                    )
        return v


class SourceDetailsParams(BaseGetSingleParams):
    """
    Parameters for getting details of a specific source.

    Used for GET /sources/{handle} endpoint.
    """

    @field_validator("extend")
    @classmethod
    def validate_extend(cls, v):
        if v is not None:
            # Convert comma-separated string to list for validation
            extend_list = [choice.strip() for choice in v.split(",")]
            for choice in extend_list:
                if choice not in SOURCE_EXTEND_CHOICES:
                    raise ValueError(
                        f"Invalid extend choice: {choice}. "
                        f"Must be one of {SOURCE_EXTEND_CHOICES}"
                    )
        return v


class SourceSaveParams(BaseDataModel):
    """
    Parameters for creating or updating a source.

    Used for POST /sources and PUT /sources/{handle} endpoints.
    """

    title: str = Field(..., description="Source title", min_length=1)
    reporef_list: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of repository references for this source"
    )
    author: Optional[str] = Field(None, description="Source author")
    pubinfo: Optional[str] = Field(None, description="Publication information")
