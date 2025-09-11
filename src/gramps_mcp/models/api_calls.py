"""
API calls enum for Gramps Web API endpoints.
"""

from enum import Enum


class ApiCalls(Enum):
    """Enumeration of all Gramps Web API endpoints."""

    # PEOPLE operations
    GET_PEOPLE = ("GET", "people/")
    POST_PEOPLE = ("POST", "people/")
    GET_PERSON = ("GET", "people/{handle}")
    PUT_PERSON = ("PUT", "people/{handle}")
    DELETE_PERSON = ("DELETE", "people/{handle}")
    GET_PERSON_TIMELINE = ("GET", "people/{handle}/timeline")
    GET_PERSON_DNA_MATCHES = ("GET", "people/{handle}/dna/matches")

    # FAMILIES operations
    GET_FAMILIES = ("GET", "families/")
    POST_FAMILIES = ("POST", "families/")
    GET_FAMILY = ("GET", "families/{handle}")
    PUT_FAMILY = ("PUT", "families/{handle}")
    DELETE_FAMILY = ("DELETE", "families/{handle}")
    GET_FAMILY_TIMELINE = ("GET", "families/{handle}/timeline")

    # EVENTS operations
    GET_EVENTS = ("GET", "events/")
    POST_EVENTS = ("POST", "events/")
    GET_EVENT = ("GET", "events/{handle}")
    PUT_EVENT = ("PUT", "events/{handle}")
    DELETE_EVENT = ("DELETE", "events/{handle}")
    GET_EVENT_SPAN = ("GET", "events/{handle1}/span/{handle2}")

    # PLACES operations
    GET_PLACES = ("GET", "places/")
    POST_PLACES = ("POST", "places/")
    GET_PLACE = ("GET", "places/{handle}")
    PUT_PLACE = ("PUT", "places/{handle}")
    DELETE_PLACE = ("DELETE", "places/{handle}")

    # CITATIONS operations
    GET_CITATIONS = ("GET", "citations/")
    POST_CITATIONS = ("POST", "citations/")
    GET_CITATION = ("GET", "citations/{handle}")
    PUT_CITATION = ("PUT", "citations/{handle}")
    DELETE_CITATION = ("DELETE", "citations/{handle}")

    # SOURCES operations
    GET_SOURCES = ("GET", "sources/")
    POST_SOURCES = ("POST", "sources/")
    GET_SOURCE = ("GET", "sources/{handle}")
    PUT_SOURCE = ("PUT", "sources/{handle}")
    DELETE_SOURCE = ("DELETE", "sources/{handle}")

    # REPOSITORIES operations
    GET_REPOSITORIES = ("GET", "repositories/")
    POST_REPOSITORIES = ("POST", "repositories/")
    GET_REPOSITORY = ("GET", "repositories/{handle}")
    PUT_REPOSITORY = ("PUT", "repositories/{handle}")
    DELETE_REPOSITORY = ("DELETE", "repositories/{handle}")

    # MEDIA operations
    GET_MEDIA = ("GET", "media/")
    POST_MEDIA = ("POST", "media/")
    GET_MEDIA_ITEM = ("GET", "media/{handle}")
    PUT_MEDIA_ITEM = ("PUT", "media/{handle}")
    DELETE_MEDIA_ITEM = ("DELETE", "media/{handle}")
    GET_MEDIA_FILE = ("GET", "media/{handle}/file")
    PUT_MEDIA_FILE = ("PUT", "media/{handle}/file")

    # NOTES operations
    GET_NOTES = ("GET", "notes/")
    POST_NOTES = ("POST", "notes/")
    GET_NOTE = ("GET", "notes/{handle}")
    PUT_NOTE = ("PUT", "notes/{handle}")
    DELETE_NOTE = ("DELETE", "notes/{handle}")

    # TAGS operations
    GET_TAGS = ("GET", "tags/")
    POST_TAGS = ("POST", "tags/")
    GET_TAG = ("GET", "tags/{handle}")
    PUT_TAG = ("PUT", "tags/{handle}")
    DELETE_TAG = ("DELETE", "tags/{handle}")

    # SEARCH operations
    GET_SEARCH = ("GET", "search/")

    # ANALYSIS operations - Relations
    GET_RELATIONS = ("GET", "relations/{handle1}/{handle2}")
    GET_RELATIONS_ALL = ("GET", "relations/{handle1}/{handle2}/all")

    # ANALYSIS operations - Living
    GET_LIVING = ("GET", "living/{handle}")
    GET_LIVING_DATES = ("GET", "living/{handle}/dates")

    # ANALYSIS operations - Timelines
    GET_TIMELINES_PEOPLE = ("GET", "timelines/people")
    GET_TIMELINES_FAMILIES = ("GET", "timelines/families")

    # ANALYSIS operations - Facts
    GET_FACTS = ("GET", "facts/")

    # MANAGEMENT operations - Transactions
    GET_TRANSACTIONS_HISTORY = ("GET", "transactions/history/")
    GET_TRANSACTION_HISTORY = ("GET", "transactions/history/{transaction_id}/")

    # MANAGEMENT operations - Types
    GET_TYPES = ("GET", "types/")
    GET_TYPES_DEFAULT = ("GET", "types/default")
    GET_TYPES_DEFAULT_DATATYPE = ("GET", "types/default/{datatype}")
    GET_TYPES_DEFAULT_MAP = ("GET", "types/default/{datatype}/map")

    # REPORTS operations
    GET_REPORTS = ("GET", "reports/")
    GET_REPORT = ("GET", "reports/{report_id}")
    GET_REPORT_FILE = ("GET", "reports/{report_id}/file")
    POST_REPORT_FILE = ("POST", "reports/{report_id}/file")
    GET_REPORT_PROCESSED = ("GET", "reports/{report_id}/file/processed/{filename}")

    # TASK operations
    GET_TASK_STATUS = ("GET", "tasks/{task_id}/")

    # HOLIDAYS operations
    GET_HOLIDAYS = ("GET", "holidays/")
    GET_HOLIDAYS_DATE = ("GET", "holidays/{country}/{year}/{month}/{day}")

    # PARSERS operations
    POST_PARSERS_DNA_MATCH = ("POST", "parsers/dna-match")

    # TREES operations
    GET_TREES = ("GET", "trees/")
    GET_TREE = ("GET", "trees/{tree_id}")

    @property
    def method(self) -> str:
        """Get HTTP method for this API call."""
        return self.value[0]

    @property
    def endpoint(self) -> str:
        """Get endpoint path for this API call."""
        return self.value[1]
