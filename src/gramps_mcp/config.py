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
Configuration management for Gramps MCP Server.

Two backends are supported:
  Web backend:    GRAMPS_API_URL + GRAMPS_USERNAME + GRAMPS_PASSWORD
  Direct backend: GRAMPS_DB_PATH (Gramps database name or path to .gpkg file)

Exactly one backend must be configured.
"""

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, HttpUrl, ValidationError, model_validator

load_dotenv()

logger = logging.getLogger(__name__)


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    # Web API backend (optional when using direct backend)
    gramps_api_url: Optional[HttpUrl] = Field(
        None, description="Base URL for Gramps Web API"
    )
    gramps_username: Optional[str] = Field(
        None, description="Username for Gramps Web API"
    )
    gramps_password: Optional[str] = Field(
        None, description="Password for Gramps Web API"
    )
    gramps_tree_id: str = Field("default", description="Family tree identifier")

    # Direct backend
    gramps_db_path: Optional[str] = Field(
        None,
        description=(
            "Gramps database name (as shown in Gramps) or absolute path to a "
            "database directory or .gpkg file. When set, the direct backend is used "
            "and no Gramps Web server is required."
        ),
    )

    @model_validator(mode="after")
    def check_backend_config(self) -> "Settings":
        """
        Validate backend credentials when a web URL is supplied.

        Starting without any backend configured is valid — the agent can
        discover and open databases at runtime via the ``list_databases``
        and ``open_database`` MCP tools.

        Args:
            None (validates self)

        Returns:
            Settings: self if valid

        Raises:
            ValueError: If web credentials are incomplete.
        """
        has_web = bool(self.gramps_api_url)
        has_direct = bool(self.gramps_db_path)

        if has_web and has_direct:
            logger.warning(
                "Both GRAMPS_API_URL and GRAMPS_DB_PATH are set. "
                "The direct backend (GRAMPS_DB_PATH) takes precedence; "
                "web credentials are ignored."
            )
        if has_web and not self.gramps_username:
            raise ValueError("GRAMPS_USERNAME is required when GRAMPS_API_URL is set.")
        if has_web and not self.gramps_password:
            raise ValueError("GRAMPS_PASSWORD is required when GRAMPS_API_URL is set.")
        return self

    @property
    def use_direct_backend(self) -> bool:
        """Return True when the direct Gramps Python API backend is active."""
        return bool(self.gramps_db_path)  # False for None and ""


def get_settings() -> Settings:
    """
    Get settings from environment variables.

    Returns:
        Settings: Validated application settings

    Raises:
        ValueError: If required environment variables are missing or invalid
    """
    try:
        return Settings(
            gramps_api_url=HttpUrl(os.environ["GRAMPS_API_URL"])
            if "GRAMPS_API_URL" in os.environ
            else None,
            gramps_username=os.environ.get("GRAMPS_USERNAME"),
            gramps_password=os.environ.get("GRAMPS_PASSWORD"),
            gramps_tree_id=os.environ.get("GRAMPS_TREE_ID", "default"),
            gramps_db_path=os.environ.get("GRAMPS_DB_PATH"),
        )
    except KeyError as e:
        raise ValueError(f"Missing required environment variable: {e}")
    except ValidationError as e:
        raise ValueError(f"Invalid configuration: {e}")
