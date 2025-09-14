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
API call parameter mapping for unified API interface.

This module maps ApiCalls enum values to their corresponding parameter models
for validation and type safety in the unified API call system.
"""

from typing import Dict, Optional, Type

from pydantic import BaseModel

from .api_calls import ApiCalls
from .parameters.base_params import BaseGetMultipleParams, BaseGetSingleParams
from .parameters.citation_params import CitationData, GetCitationsParams
from .parameters.event_params import EventSaveParams, EventSearchParams, EventSpanParams
from .parameters.facts_params import FactsParams
from .parameters.family_params import FamilySaveParams, FamilyTimelineParams
from .parameters.holidays_params import HolidaysParams
from .parameters.living_params import LivingParams
from .parameters.media_params import MediaFileParams, MediaSaveParams, MediaSearchParams
from .parameters.note_params import NoteParams, NoteSaveParams, NotesParams
from .parameters.parser_params import DnaMatchParseParams
from .parameters.people_params import (
    PersonData,
    PersonDnaMatchesParams,
    PersonTimelineParams,
)
from .parameters.place_params import PlaceSaveParams
from .parameters.relations_params import RelationParams
from .parameters.reports_params import ReportFileParams, ReportGetParams
from .parameters.repository_params import (
    RepositoriesParams,
    RepositoryData,
    RepositoryParams,
)
from .parameters.search_params import SearchParams
from .parameters.source_params import (
    SourceDetailsParams,
    SourceSaveParams,
    SourceSearchParams,
)
from .parameters.tag_params import TagSaveParams, TagSearchParams
from .parameters.timeline_params import FamiliesTimelineParams, PeopleTimelineParams
from .parameters.transactions_params import (
    TransactionHistoryByIdParams,
    TransactionHistoryParams,
)
from .parameters.types_params import TypesParams

# Mapping of API calls to their parameter models
API_CALL_PARAMS: Dict[ApiCalls, Optional[Type[BaseModel]]] = {
    # PEOPLE operations
    ApiCalls.GET_PEOPLE: BaseGetMultipleParams,
    ApiCalls.POST_PEOPLE: PersonData,
    ApiCalls.GET_PERSON: BaseGetSingleParams,
    ApiCalls.PUT_PERSON: PersonData,
    ApiCalls.DELETE_PERSON: None,  # Only needs handle (via URL)
    ApiCalls.GET_PERSON_TIMELINE: PersonTimelineParams,
    ApiCalls.GET_PERSON_DNA_MATCHES: PersonDnaMatchesParams,
    # FAMILIES operations
    ApiCalls.GET_FAMILIES: BaseGetMultipleParams,
    ApiCalls.POST_FAMILIES: FamilySaveParams,
    ApiCalls.GET_FAMILY: BaseGetSingleParams,
    ApiCalls.PUT_FAMILY: FamilySaveParams,
    ApiCalls.DELETE_FAMILY: None,  # Only needs handle (via URL)
    ApiCalls.GET_FAMILY_TIMELINE: FamilyTimelineParams,
    # EVENTS operations
    ApiCalls.GET_EVENTS: EventSearchParams,
    ApiCalls.POST_EVENTS: EventSaveParams,
    ApiCalls.GET_EVENT: BaseGetSingleParams,
    ApiCalls.PUT_EVENT: EventSaveParams,
    ApiCalls.DELETE_EVENT: None,  # Only needs handle (via URL)
    ApiCalls.GET_EVENT_SPAN: EventSpanParams,
    # PLACES operations
    ApiCalls.GET_PLACES: BaseGetMultipleParams,
    ApiCalls.POST_PLACES: PlaceSaveParams,
    ApiCalls.GET_PLACE: BaseGetSingleParams,
    ApiCalls.PUT_PLACE: PlaceSaveParams,
    ApiCalls.DELETE_PLACE: None,  # Only needs handle (via URL)
    # CITATIONS operations
    ApiCalls.GET_CITATIONS: GetCitationsParams,
    ApiCalls.POST_CITATIONS: CitationData,
    ApiCalls.GET_CITATION: BaseGetSingleParams,
    ApiCalls.PUT_CITATION: CitationData,
    ApiCalls.DELETE_CITATION: None,  # Only needs handle (via URL)
    # SOURCES operations
    ApiCalls.GET_SOURCES: SourceSearchParams,
    ApiCalls.POST_SOURCES: SourceSaveParams,
    ApiCalls.GET_SOURCE: SourceDetailsParams,
    ApiCalls.PUT_SOURCE: SourceSaveParams,
    ApiCalls.DELETE_SOURCE: None,  # Only needs handle (via URL)
    # REPOSITORIES operations
    ApiCalls.GET_REPOSITORIES: RepositoriesParams,
    ApiCalls.POST_REPOSITORIES: RepositoryData,
    ApiCalls.GET_REPOSITORY: RepositoryParams,
    ApiCalls.PUT_REPOSITORY: RepositoryData,
    ApiCalls.DELETE_REPOSITORY: None,  # Only needs handle (via URL)
    # MEDIA operations
    ApiCalls.GET_MEDIA: MediaSearchParams,
    ApiCalls.POST_MEDIA: None,  # File upload only, no JSON params
    ApiCalls.GET_MEDIA_ITEM: BaseGetSingleParams,
    ApiCalls.PUT_MEDIA_ITEM: MediaSaveParams,
    ApiCalls.DELETE_MEDIA_ITEM: None,  # Only needs handle (via URL)
    ApiCalls.GET_MEDIA_FILE: MediaFileParams,
    ApiCalls.PUT_MEDIA_FILE: MediaFileParams,
    # NOTES operations
    ApiCalls.GET_NOTES: NotesParams,
    ApiCalls.POST_NOTES: NoteSaveParams,
    ApiCalls.GET_NOTE: NoteParams,
    ApiCalls.PUT_NOTE: NoteSaveParams,
    ApiCalls.DELETE_NOTE: None,  # Only needs handle (via URL)
    # TAGS operations
    ApiCalls.GET_TAGS: TagSearchParams,
    ApiCalls.POST_TAGS: TagSaveParams,
    ApiCalls.GET_TAG: None,  # Only needs handle (via URL)
    ApiCalls.PUT_TAG: TagSaveParams,
    ApiCalls.DELETE_TAG: None,  # Only needs handle (via URL)
    # SEARCH operations
    ApiCalls.GET_SEARCH: SearchParams,
    # RELATIONS operations
    ApiCalls.GET_RELATIONS: RelationParams,
    ApiCalls.GET_RELATIONS_ALL: RelationParams,
    # LIVING operations
    ApiCalls.GET_LIVING: LivingParams,
    ApiCalls.GET_LIVING_DATES: LivingParams,
    # TIMELINES operations
    ApiCalls.GET_TIMELINES_PEOPLE: PeopleTimelineParams,
    ApiCalls.GET_TIMELINES_FAMILIES: FamiliesTimelineParams,
    # FACTS operations
    ApiCalls.GET_FACTS: FactsParams,
    # TRANSACTIONS operations
    ApiCalls.GET_TRANSACTIONS_HISTORY: TransactionHistoryParams,
    ApiCalls.GET_TRANSACTION_HISTORY: TransactionHistoryByIdParams,
    # TYPES operations
    ApiCalls.GET_TYPES: None,
    ApiCalls.GET_TYPES_DEFAULT: None,
    ApiCalls.GET_TYPES_DEFAULT_DATATYPE: TypesParams,
    ApiCalls.GET_TYPES_DEFAULT_MAP: TypesParams,
    # REPORTS operations
    ApiCalls.GET_REPORTS: ReportGetParams,
    ApiCalls.GET_REPORT: ReportGetParams,
    ApiCalls.GET_REPORT_FILE: ReportFileParams,
    ApiCalls.POST_REPORT_FILE: ReportFileParams,
    ApiCalls.GET_REPORT_PROCESSED: None,
    # HOLIDAYS operations
    ApiCalls.GET_HOLIDAYS: None,
    ApiCalls.GET_HOLIDAYS_DATE: HolidaysParams,
    # PARSERS operations
    ApiCalls.POST_PARSERS_DNA_MATCH: DnaMatchParseParams,
    # TREES operations
    ApiCalls.GET_TREES: None,
    ApiCalls.GET_TREE: None,
}


def get_param_model(api_call: ApiCalls) -> Optional[Type[BaseModel]]:
    """
    Get the parameter model class for a given API call.

    Args:
        api_call: The API call enum value

    Returns:
        The corresponding parameter model class, or None if no parameters needed
    """
    return API_CALL_PARAMS.get(api_call)


def validate_api_call_params(api_call: ApiCalls, params: dict) -> BaseModel:
    """
    Validate parameters for a given API call using its parameter model.

    Args:
        api_call: The API call enum value
        params: Dictionary of parameters to validate

    Returns:
        Validated parameter model instance

    Raises:
        ValueError: If no parameter model is defined for the API call
        ValidationError: If parameters don't match the model schema
    """
    param_model = get_param_model(api_call)

    if param_model is None:
        if params:
            raise ValueError(
                f"API call {api_call.name} does not accept parameters, "
                f"but parameters were provided: {params}"
            )
        return None

    return param_model(**params)
