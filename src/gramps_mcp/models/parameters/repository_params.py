"""
Pydantic models for repository-related operations.

API calls supported in this category:
- GET_REPOSITORIES: Get information about multiple repositories
- POST_REPOSITORIES: Add a new repository to the database
- GET_REPOSITORY: Get information about a specific repository
- PUT_REPOSITORY: Update the repository
- DELETE_REPOSITORY: Delete the repository
"""

from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from .base_params import BaseDataModel, BaseGetMultipleParams, BaseGetSingleParams

# Repository-specific constants
REPOSITORY_EXTEND_CHOICES = ["all", "note_list", "tag_list", "backlinks"]

REPOSITORY_SORT_KEYS = ["change", "gramps_id", "name", "private", "type"]


class RepositoriesParams(BaseGetMultipleParams):
    """Parameters for getting multiple repositories information from Gramps API."""

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, v):
        if v is not None:
            # Parse comma-separated sort keys
            sort_keys = [key.strip().lstrip("-") for key in v.split(",")]
            for key in sort_keys:
                if key not in REPOSITORY_SORT_KEYS:
                    raise ValueError(
                        f"Invalid sort key: {key}. "
                        f"Must be one of {REPOSITORY_SORT_KEYS}"
                    )
        return v

    @field_validator("extend")
    @classmethod
    def validate_extend(cls, v):
        if v is not None:
            # Convert comma-separated string to list for validation
            extend_list = [choice.strip() for choice in v.split(",")]
            for choice in extend_list:
                if choice not in REPOSITORY_EXTEND_CHOICES:
                    raise ValueError(
                        f"Invalid extend choice: {choice}. "
                        f"Must be one of {REPOSITORY_EXTEND_CHOICES}"
                    )
        return v


class RepositoryParams(BaseGetSingleParams):
    """Parameters for getting a single repository by handle from Gramps API."""

    @field_validator("extend")
    @classmethod
    def validate_extend(cls, v):
        if v is not None:
            # Convert comma-separated string to list for validation
            extend_list = [choice.strip() for choice in v.split(",")]
            for choice in extend_list:
                if choice not in REPOSITORY_EXTEND_CHOICES:
                    raise ValueError(
                        f"Invalid extend choice: {choice}. "
                        f"Must be one of {REPOSITORY_EXTEND_CHOICES}"
                    )
        return v


class RepositoryData(BaseDataModel):
    """Model for creating or updating a repository in Gramps API."""

    name: str = Field(..., description="Repository name")
    type: str = Field(
        ..., description="Repository type (e.g., 'Archive', 'Library', 'Church', etc.)"
    )
    urls: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of URLs associated with the repository"
    )
