"""
Configuration management for Gramps MCP Server.
"""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, HttpUrl, ValidationError

# Load environment variables from .env file
load_dotenv()


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    # Gramps Web API Configuration
    gramps_api_url: HttpUrl = Field(..., description="Base URL for Gramps Web API")
    gramps_username: str = Field(..., description="Username for Gramps Web API")
    gramps_password: str = Field(..., description="Password for Gramps Web API")
    gramps_tree_id: str = Field(..., description="Family tree identifier")


def get_settings() -> Settings:
    """Get settings from environment variables."""
    try:
        return Settings(
            gramps_api_url=HttpUrl(os.environ["GRAMPS_API_URL"]),
            gramps_username=os.environ["GRAMPS_USERNAME"],
            gramps_password=os.environ["GRAMPS_PASSWORD"],
            gramps_tree_id=os.environ["GRAMPS_TREE_ID"],
        )
    except KeyError as e:
        raise ValueError(f"Missing required environment variable: {e}")
    except ValidationError as e:
        raise ValueError(f"Invalid configuration: {e}")
