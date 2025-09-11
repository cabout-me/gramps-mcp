"""
Family data handler for Gramps MCP operations.

Provides clean, direct formatting of family data from handles.
"""

import logging

from ..models.api_calls import ApiCalls
from .date_handler import format_date
from .place_handler import format_place

logger = logging.getLogger(__name__)


async def format_family(client, tree_id: str, handle: str) -> str:
    """
    Format family data with members and basic details.

    Args:
        client: Gramps API client instance
        tree_id (str): Family tree identifier
        handle (str): Family handle

    Returns:
        str: Formatted family string with members and details
    """
    if not handle:
        return "• **Family**\n  No handle provided\n\n"

    try:
        # Get family data with extended information
        family_data = await client.make_api_call(
            ApiCalls.GET_FAMILY,
            tree_id=tree_id,
            handle=handle,
            params={"extend": "all"},
        )
        if not family_data:
            return f"• **Family {handle}**\n  Family not found\n\n"

        gramps_id = family_data.get("gramps_id", "")
        result = ""

        # First line: Father: Name (Gender) - ID | Mother: Name (Gender) - ID
        # - FamilyID - [family_handle]
        family_members = []

        # Get father
        father_handle = family_data.get("father_handle", "")
        if father_handle:
            try:
                father_data = await client.make_api_call(
                    ApiCalls.GET_PERSON, tree_id=tree_id, handle=father_handle
                )
                if father_data:
                    father_name = _extract_person_name(father_data)
                    father_gender = _get_gender_letter(father_data.get("gender", 2))
                    father_id = father_data.get("gramps_id", "")
                    family_members.append(
                        f"Father: {father_name} ({father_gender}) - {father_id}"
                    )
            except Exception as e:
                logger.debug(f"Failed to fetch father {father_handle}: {e}")

        # Get mother
        mother_handle = family_data.get("mother_handle", "")
        if mother_handle:
            try:
                mother_data = await client.make_api_call(
                    ApiCalls.GET_PERSON, tree_id=tree_id, handle=mother_handle
                )
                if mother_data:
                    mother_name = _extract_person_name(mother_data)
                    mother_gender = _get_gender_letter(mother_data.get("gender", 2))
                    mother_id = mother_data.get("gramps_id", "")
                    family_members.append(
                        f"Mother: {mother_name} ({mother_gender}) - {mother_id}"
                    )
            except Exception as e:
                logger.debug(f"Failed to fetch mother {mother_handle}: {e}")

        # First line with family ID and handle
        if family_members:
            result += f"{' | '.join(family_members)} - {gramps_id} - [{handle}]\n"
        else:
            result += f"{gramps_id} - [{handle}]\n"

        # Marriage and divorce events
        extended = family_data.get("extended", {})
        events = extended.get("events", [])
        event_ref_list = family_data.get("event_ref_list", [])

        for i, event_ref in enumerate(event_ref_list):
            if i < len(events):
                event = events[i]
                event_type = event.get("type", "")

                if event_type.lower() == "marriage":
                    marriage_date = format_date(event.get("date", {}))
                    marriage_place = await format_place(
                        client, tree_id, event.get("place", ""), inline=True
                    )
                    if marriage_date or marriage_place:
                        result += f"Married: {marriage_date}"
                        if marriage_place:
                            result += f" - {marriage_place}"
                        result += "\n"

                elif event_type.lower() == "divorce":
                    divorce_date = format_date(event.get("date", {}))
                    divorce_place = await format_place(
                        client, tree_id, event.get("place", ""), inline=True
                    )
                    if divorce_date or divorce_place:
                        result += f"Divorced: {divorce_date}"
                        if divorce_place:
                            result += f" - {divorce_place}"
                        result += "\n"

        # Children
        child_ref_list = family_data.get("child_ref_list", [])
        if child_ref_list:
            child_names = []
            for child_ref in child_ref_list:
                child_handle = child_ref.get("ref", "")
                if child_handle:
                    try:
                        child_data = await client.make_api_call(
                            ApiCalls.GET_PERSON, tree_id=tree_id, handle=child_handle
                        )
                        if child_data:
                            child_name = _extract_person_name(child_data)
                            child_gender = _get_gender_letter(
                                child_data.get("gender", 2)
                            )
                            child_id = child_data.get("gramps_id", "")
                            child_names.append(
                                f"{child_name} ({child_gender}) - {child_id}"
                            )
                    except Exception as e:
                        logger.debug(f"Failed to fetch child {child_handle}: {e}")

            if child_names:
                result += f"Children: {', '.join(child_names)}\n"

        # Events (all events with roles)
        event_list = []
        for i, event_ref in enumerate(event_ref_list):
            if i < len(events):
                event = events[i]
                event_type = event.get("type", "")
                event_gramps_id = event.get("gramps_id", "")

                # Get role from event_ref
                role = event_ref.get("role", "") if isinstance(event_ref, dict) else ""
                if role:
                    event_list.append(f"{event_type}, {role} ({event_gramps_id})")
                else:
                    event_list.append(f"{event_type} ({event_gramps_id})")

        if event_list:
            result += f"Events: {', '.join(event_list)}\n"

        # Attached media
        media_list = family_data.get("media_list", [])
        if media_list:
            media_ids = []
            for media_ref in media_list:
                media_handle = (
                    media_ref.get("ref", "")
                    if isinstance(media_ref, dict)
                    else media_ref
                )
                if media_handle:
                    try:
                        media_data = await client.make_api_call(
                            api_call=ApiCalls.GET_MEDIA,
                            tree_id=tree_id,
                            handle=media_handle,
                        )
                        if media_data:
                            media_gramps_id = media_data.get("gramps_id", "")
                            if media_gramps_id:
                                media_ids.append(media_gramps_id)
                    except Exception:
                        continue

            if media_ids:
                result += f"Attached media: {', '.join(media_ids)}\n"

        # Attached notes
        note_list = family_data.get("note_list", [])
        if note_list:
            note_ids = []
            for note_handle in note_list:
                try:
                    note_data = await client.make_api_call(
                        api_call=ApiCalls.GET_NOTE, tree_id=tree_id, handle=note_handle
                    )
                    if note_data:
                        note_gramps_id = note_data.get("gramps_id", "")
                        if note_gramps_id:
                            note_ids.append(note_gramps_id)
                except Exception:
                    continue

            if note_ids:
                result += f"Attached notes: {', '.join(note_ids)}\n"

        # URLs
        urls = family_data.get("urls", [])
        if urls:
            for url in urls:
                if isinstance(url, dict):
                    url_path = url.get("path", "")
                    url_desc = url.get("description", "")
                    if url_path:
                        if url_desc:
                            result += f"{url_path} - {url_desc}\n"
                        else:
                            result += f"{url_path}\n"

        return result + "\n"

    except Exception as e:
        logger.debug(f"Failed to format family {handle}: {e}")
        return f"• **Family {handle}**\n  Error formatting family: {str(e)}\n\n"


def _extract_person_name(person_data: dict) -> str:
    """Extract full name from person data."""
    primary_name = person_data.get("primary_name", {})
    if primary_name:
        given_name = primary_name.get("first_name", "")
        surname_list = primary_name.get("surname_list", [])
        surname = surname_list[0].get("surname", "") if surname_list else ""
        full_name = f"{given_name} {surname}".strip()
        return full_name if full_name else ""
    return ""


def _get_gender_letter(gender: int) -> str:
    """Convert gender number to letter."""
    return {0: "F", 1: "M", 2: "U"}.get(gender, "U")
