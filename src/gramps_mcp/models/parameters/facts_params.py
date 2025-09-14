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
Pydantic models for facts-related operations.

API calls supported in this category:
- GET_FACTS: Get interesting facts about records in the tree
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LivingProxy(str, Enum):
    """Enumeration for living proxy options."""

    INCLUDE_ALL = "IncludeAll"
    FULL_NAME_ONLY = "FullNameOnly"
    LAST_NAME_ONLY = "LastNameOnly"
    REPLACE_COMPLETE_NAME = "ReplaceCompleteName"
    EXCLUDE_ALL = "ExcludeAll"


class PersonFilter(str, Enum):
    """Enumeration for built-in person filters."""

    DESCENDANTS = "Descendants"
    DESCENDANT_FAMILIES = "DescendantFamilies"
    ANCESTORS = "Ancestors"
    COMMON_ANCESTOR = "CommonAncestor"


class FactsParams(BaseModel):
    """Parameters for getting interesting facts about records in the tree."""

    gramps_id: Optional[str] = Field(
        None,
        description=(
            "The Gramps identifier of the person to whom a built in person "
            "filter should be applied if one was provided"
        ),
    )

    handle: Optional[str] = Field(
        None,
        description=(
            "The handle identifying the person to whom a built in person "
            "filter should be applied if one was provided. If gramps_id was "
            "also provided that will always take precedence"
        ),
    )

    living: LivingProxy = Field(
        LivingProxy.INCLUDE_ALL,
        description=(
            "The name of a built in proxy function controlling how people "
            "determined to be living should be handled"
        ),
    )

    person: Optional[str] = Field(
        None,
        description=(
            "If provided the name of a built in or a custom filter to apply. "
            "Built in filters are applied with respect to a person so a "
            "gramps_id or handle must also be provided separately"
        ),
    )

    private: bool = Field(
        False,
        description="Indicates whether or not to exclude all records marked private",
    )

    rank: int = Field(
        1,
        ge=1,
        description=(
            "Determines how many objects should be returned for ranked "
            "statistics items"
        ),
    )

    @field_validator("person")
    @classmethod
    def validate_person_filter(cls, v):
        """Validate person filter if it's a built-in filter."""
        if v is not None:
            # Check if it's one of the built-in filters
            try:
                PersonFilter(v)
            except ValueError:
                # If not a built-in filter, assume it's a custom filter name
                # and allow it
                pass
        return v
