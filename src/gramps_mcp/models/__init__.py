"""
Pydantic models for MCP tool parameters and validation.

This package contains all data models for the genealogy tools organized by feature.
"""

# Import API calls enum
from .api_calls import ApiCalls

# Import base models
from .parameters.base_params import (
    BaseDataModel,
    BaseGetMultipleParams,
    BaseGetSingleParams,
)

# Import citation models
from .parameters.citation_params import CitationData, GetCitationsParams

# Import event models
from .parameters.event_params import EventSaveParams, EventSearchParams, EventSpanParams

# Import additional parameter models
from .parameters.facts_params import FactsParams

# Import family models
from .parameters.family_params import FamilySaveParams, FamilyTimelineParams
from .parameters.holidays_params import HolidaysParams
from .parameters.living_params import LivingParams

# Import media models
from .parameters.media_params import MediaFileParams, MediaSaveParams, MediaSearchParams

# Import note models
from .parameters.note_params import NoteParams, NoteSaveParams, NotesParams
from .parameters.parser_params import DnaMatchParseParams

# Import existing parameter models
from .parameters.people_params import (
    PersonData,
    PersonDnaMatchesParams,
    PersonTimelineParams,
)

# Import place models
from .parameters.place_params import (
    PlaceDetailsParams,
    PlaceSaveParams,
    PlaceSearchParams,
)
from .parameters.relations_params import RelationParams

# Import reports models
from .parameters.reports_params import (
    ReportFileParams,
    ReportGetParams,
)

# Import repository models
from .parameters.repository_params import (
    RepositoriesParams,
    RepositoryData,
    RepositoryParams,
)

# Import search models
from .parameters.search_params import SearchParams
from .parameters.simple_params import (
    EntityType,
    GetEntityType,
    SimpleFindParams,
    SimpleGetParams,
    SimpleSearchParams,
)

# Import source models
from .parameters.source_params import (
    SourceDetailsParams,
    SourceSaveParams,
    SourceSearchParams,
)

# Import tag models
from .parameters.tag_params import TagSaveParams, TagSearchParams
from .parameters.timeline_params import (
    FamiliesTimelineParams,
    PeopleTimelineParams,
)

# Import remaining parameter models
from .parameters.transactions_params import (
    TransactionHistoryByIdParams,
    TransactionHistoryParams,
)
from .parameters.types_params import TypesParams

__all__ = [
    "ApiCalls",
    # Base params
    "BaseGetSingleParams",
    "BaseGetMultipleParams",
    "BaseDataModel",
    # Search params
    "SearchParams",
    "EventSearchParams",
    "MediaSearchParams",
    "PlaceSearchParams",
    "SourceSearchParams",
    "TagSearchParams",
    "GetCitationsParams",
    # Save params
    "PersonData",
    "FamilySaveParams",
    "EventSaveParams",
    "PlaceSaveParams",
    "SourceSaveParams",
    "CitationData",
    "NoteSaveParams",
    "MediaSaveParams",
    "TagSaveParams",
    "RepositoryData",
    # Detail params
    "PlaceDetailsParams",
    "SourceDetailsParams",
    "RepositoryParams",
    "NoteParams",
    "NotesParams",
    "MediaFileParams",
    # Timeline params
    "PersonTimelineParams",
    "FamilyTimelineParams",
    "PeopleTimelineParams",
    "FamiliesTimelineParams",
    # Other params
    "PersonDnaMatchesParams",
    "EventSpanParams",
    "RepositoriesParams",
    "RelationParams",
    "LivingParams",
    "FactsParams",
    "TransactionHistoryParams",
    "TransactionHistoryByIdParams",
    "TypesParams",
    "ReportGetParams",
    "ReportFileParams",
    "HolidaysParams",
    "DnaMatchParseParams",
    # Simple params
    "SimpleFindParams",
    "SimpleSearchParams",
    "SimpleGetParams",
    # Enums
    "EntityType",
    "GetEntityType",
]
