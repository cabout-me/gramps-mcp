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
Person detail handler for Gramps MCP operations.
"""

from ..models.api_calls import ApiCalls
from .date_handler import format_date
from .place_handler import format_place


async def format_person_detail(client, tree_id: str, handle: str) -> str:
    """Format comprehensive person data with timeline and citations."""
    # Get person data
    person_data = await client.make_api_call(
        ApiCalls.GET_PERSON, tree_id=tree_id, handle=handle, params={"extend": "all"}
    )

    # Get person timeline
    timeline_data = await client.make_api_call(
        ApiCalls.GET_PERSON_TIMELINE,
        tree_id=tree_id,
        handle=handle,
        params={"ratings": True},  # Include citation confidence
    )

    result = "=== PERSON DETAILS ===\n"

    # Extract basic info
    gramps_id = person_data.get("gramps_id", "")
    name = _extract_person_name(person_data)
    gender_display = _get_gender_letter(person_data.get("gender", 2))

    result += f"{name} ({gender_display}) - {gramps_id} - [{handle}]\n"

    # Birth and death from extended data
    extended = person_data.get("extended", {})
    events = extended.get("events", [])

    # Birth event
    birth_ref_index = person_data.get("birth_ref_index", -1)
    if birth_ref_index >= 0 and birth_ref_index < len(events):
        birth_event = events[birth_ref_index]
        birth_date = format_date(birth_event.get("date", {}))
        birth_place = await format_place(
            client, tree_id, birth_event.get("place", ""), inline=True
        )
        result += f"Born: {birth_date} - {birth_place}\n"

    # Death event
    death_ref_index = person_data.get("death_ref_index", -1)
    if death_ref_index >= 0 and death_ref_index < len(events):
        death_event = events[death_ref_index]
        death_date = format_date(death_event.get("date", {}))
        death_place = await format_place(
            client, tree_id, death_event.get("place", ""), inline=True
        )
        result += f"Died: {death_date} - {death_place}\n"

    # Relations section
    result += "\nRELATIONS:\n"

    # Parents section
    result += "Parents:\n"
    parent_family_list = person_data.get("parent_family_list", [])

    for family_handle in parent_family_list:
        try:
            family_data = await client.make_api_call(
                ApiCalls.GET_FAMILY,
                tree_id=tree_id,
                handle=family_handle,
                params={"extend": "all"},
            )
            extended = family_data.get("extended", {})

            # Father
            father = extended.get("father", {})
            if father:
                father_name = _extract_person_name(father)
                father_id = father.get("gramps_id", "")
                father_birth, father_death = await _get_birth_death_dates(
                    client, tree_id, father
                )
                dates = ", ".join(filter(None, [father_birth, father_death]))
                result += f"- {father_name} - {father_id} - {dates}\n"

            # Mother
            mother = extended.get("mother", {})
            if mother:
                mother_name = _extract_person_name(mother)
                mother_id = mother.get("gramps_id", "")
                mother_birth, mother_death = await _get_birth_death_dates(
                    client, tree_id, mother
                )
                dates = ", ".join(filter(None, [mother_birth, mother_death]))
                result += f"- {mother_name} - {mother_id} - {dates}\n"

            # Siblings (other children in same family)
            children = extended.get("children", [])
            siblings = [
                child for child in children if child.get("gramps_id", "") != gramps_id
            ]
            if siblings:
                result += "Siblings:\n"
                for sibling in siblings:
                    sibling_name = _extract_person_name(sibling)
                    sibling_id = sibling.get("gramps_id", "")
                    sibling_birth, sibling_death = await _get_birth_death_dates(
                        client, tree_id, sibling
                    )
                    dates = ", ".join(filter(None, [sibling_birth, sibling_death]))
                    result += f"- {sibling_name} - {sibling_id} - {dates}\n"

        except Exception:
            continue

    # Spouses and children
    family_list = person_data.get("family_list", [])
    for family_handle in family_list:
        try:
            family_data = await client.make_api_call(
                ApiCalls.GET_FAMILY,
                tree_id=tree_id,
                handle=family_handle,
                params={"extend": "all"},
            )
            extended = family_data.get("extended", {})

            # Determine spouse (father or mother that's not this person)
            father = extended.get("father", {})
            mother = extended.get("mother", {})

            spouse = None
            if father and father.get("gramps_id", "") != gramps_id:
                spouse = father
            elif mother and mother.get("gramps_id", "") != gramps_id:
                spouse = mother

            if spouse:
                spouse_name = _extract_person_name(spouse)
                spouse_id = spouse.get("gramps_id", "")
                spouse_birth, spouse_death = await _get_birth_death_dates(
                    client, tree_id, spouse
                )
                dates = ", ".join(filter(None, [spouse_birth, spouse_death]))
                result += f"Spouse:\n- {spouse_name} - {spouse_id} - {dates}\n"

                # Children of this spouse
                children = extended.get("children", [])
                if children:
                    result += "Children:\n"
                    for child in children:
                        child_name = _extract_person_name(child)
                        child_id = child.get("gramps_id", "")
                        child_birth, child_death = await _get_birth_death_dates(
                            client, tree_id, child
                        )
                        dates = ", ".join(filter(None, [child_birth, child_death]))
                        result += f"- {child_name} - {child_id} - {dates}\n"
        except Exception:
            continue

    # Timeline section
    result += "\nTIMELINE:\n"
    if timeline_data:
        for timeline_event in timeline_data:
            if not isinstance(timeline_event, dict):
                continue

            # Basic event info from timeline
            event_type = timeline_event.get("type", "Unknown")
            event_id = timeline_event.get("gramps_id", "")
            role = timeline_event.get("role", "Primary")
            event_handle = timeline_event.get("handle", "")

            # Get properly formatted date using format_date function
            event_date = "date unknown"
            event_data = None
            if event_handle:
                try:
                    event_data = await client.make_api_call(
                        ApiCalls.GET_EVENT, tree_id=tree_id, handle=event_handle
                    )
                    event_date = format_date(event_data.get("date", {}))
                except Exception:
                    # Fallback to timeline date if event fetch fails
                    event_date = timeline_event.get("date", "date unknown")

            # Place - use display_name directly from timeline data
            place_data = timeline_event.get("place", {})
            place_name = (
                place_data.get("display_name", "")
                if isinstance(place_data, dict)
                else ""
            )
            place_part = f"({place_name})" if place_name else "()"

            # Participant info - extract from person data in timeline
            participant_name = ""
            participant_id = ""
            person_data_in_timeline = timeline_event.get("person", {})

            if person_data_in_timeline:
                relationship = person_data_in_timeline.get("relationship", "")
                if relationship == "self":
                    # This person's event
                    participant_name = _extract_person_name(person_data)
                    participant_id = person_data.get("gramps_id", "")
                else:
                    # Other person's event - use data from timeline
                    given_name = person_data_in_timeline.get("name_given", "")
                    surname = person_data_in_timeline.get("name_surname", "")
                    participant_name = f"{given_name} {surname}".strip()
                    participant_id = person_data_in_timeline.get("gramps_id", "")

            # Format the timeline entry
            participant_part = (
                f", {participant_name} {participant_id}, {role}"
                if participant_name
                else f", {role}"
            )
            result += (
                f"- {event_date} {place_part} - {event_id} : "
                f"{event_type}{participant_part}\n"
            )

            # Add citations if we have event data - reuse the event_data from above
            if event_data:
                try:
                    citation_list = event_data.get("citation_list", [])
                    citation_ids = []
                    for citation_handle in citation_list:
                        citation_data = await client.make_api_call(
                            ApiCalls.GET_CITATION,
                            tree_id=tree_id,
                            handle=citation_handle,
                        )
                        citation_id = citation_data.get("gramps_id", "")
                        if citation_id:
                            citation_ids.append(citation_id)

                    if citation_ids:
                        result += f"  Citations: {', '.join(citation_ids)}\n"
                except Exception:
                    pass

    # Attached media section
    result += "\nAttached media:\n"
    media_list = person_data.get("media_list", [])
    for media_ref in media_list:
        media_handle = media_ref.get("ref", "")
        if media_handle:
            media_data = await client.make_api_call(
                ApiCalls.GET_MEDIA_ITEM, tree_id=tree_id, handle=media_handle
            )
            media_desc = media_data.get("desc", "")
            media_id = media_data.get("gramps_id", "")
            result += f"- {media_desc} ({media_id})\n"

    # Attached notes section
    result += "\nAttached notes:\n"
    note_list = person_data.get("note_list", [])
    for note_handle in note_list:
        note_data = await client.make_api_call(
            ApiCalls.GET_NOTE, tree_id=tree_id, handle=note_handle
        )
        note_type = note_data.get("type", "")
        note_id = note_data.get("gramps_id", "")
        note_text = note_data.get("text", "")[:50]
        if len(note_data.get("text", "")) > 50:
            note_text += "..."
        result += f"- {note_type}: {note_text} ({note_id})\n"

    return result


def _extract_person_name(person_data: dict) -> str:
    """Extract full name from person data."""
    primary_name = person_data.get("primary_name", {})
    if primary_name:
        given_name = primary_name.get("first_name", "")
        surname_list = primary_name.get("surname_list", [])
        surname = surname_list[0].get("surname", "") if surname_list else ""
        return f"{given_name} {surname}".strip()
    return "Unknown"


def _get_gender_letter(gender: int) -> str:
    """Convert gender number to letter."""
    return {0: "F", 1: "M", 2: "U"}.get(gender, "U")


async def _get_birth_death_dates(client, tree_id: str, person_data: dict) -> tuple:
    """Get birth and death dates for a person."""
    person_handle = person_data.get("handle", "")
    if not person_handle:
        return "", ""

    try:
        # Get person with extended data to access events
        full_person_data = await client.make_api_call(
            ApiCalls.GET_PERSON,
            tree_id=tree_id,
            handle=person_handle,
            params={"extend": "all"},
        )

        extended = full_person_data.get("extended", {})
        events = extended.get("events", [])

        birth_date = ""
        death_date = ""

        # Check for birth event
        birth_ref_index = full_person_data.get("birth_ref_index", -1)
        if birth_ref_index >= 0 and birth_ref_index < len(events):
            birth_event = events[birth_ref_index]
            birth_date = format_date(birth_event.get("date", {}))

        # Check for death event
        death_ref_index = full_person_data.get("death_ref_index", -1)
        if death_ref_index >= 0 and death_ref_index < len(events):
            death_event = events[death_ref_index]
            death_date = format_date(death_event.get("date", {}))

        # If still living, show as such
        if full_person_data.get("living", False):
            death_date = "Living"

        return birth_date, death_date

    except Exception:
        return "", ""
