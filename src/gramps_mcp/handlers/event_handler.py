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
Event data handler for Gramps MCP operations.

Provides clean, direct formatting of event data from handles.
"""

import logging

from ..models.api_calls import ApiCalls
from .date_handler import format_date
from .place_handler import format_place

logger = logging.getLogger(__name__)


async def format_event(
    client, tree_id: str, handle: str, event_label: str = None
) -> str:
    """
    Format event data with type, date, place, and participants.

    Args:
        client: Gramps API client instance
        tree_id (str): Family tree identifier
        handle (str): Event handle
        event_label (str, optional): Optional label for inline display
            ("Born", "Died", etc.)

    Returns:
        str: Formatted event string (full format if no label, inline if label provided)
    """
    if not handle:
        if event_label:
            return None  # For inline use
        return "• **Unknown Event**\n  No handle provided\n\n"

    try:
        event_data = await client.make_api_call(
            api_call=ApiCalls.GET_EVENT,
            tree_id=tree_id,
            handle=handle,
            params={"extend": "backlinks", "backlinks": True},
        )
        if not event_data:
            if event_label:
                return None  # For inline use
            return f"• **Event {handle}**\n  Event not found\n\n"

        # Format date using date handler
        event_date = format_date(event_data.get("date", {}))

        # Format place using place handler
        event_place = await format_place(
            client, tree_id, event_data.get("place", ""), inline=True
        )

        # If event_label is provided, return inline format (for life events)
        if event_label:
            return f"{event_label}: {event_date}, {event_place}"

        # Otherwise return full search result format
        gramps_id = event_data.get("gramps_id", "")
        event_type = event_data.get("type", "Unknown Event")
        citation_list = event_data.get("citation_list", [])
        note_list = event_data.get("note_list", [])

        # Get participants from extended backlinks
        primary_person_name = ""
        participants = []

        extended = event_data.get("extended", {})
        backlinks = extended.get("backlinks", {})

        # Check for direct person backlinks (individual events like birth, death)
        if "person" in backlinks:
            people = backlinks["person"]
            for person in people:
                person_gramps_id = person.get("gramps_id", "")
                person_name = person.get("primary_name", {})
                first_name = person_name.get("first_name", "")
                surname_list = person_name.get("surname_list", [])
                surname = surname_list[0].get("surname", "") if surname_list else ""
                full_name = f"{first_name} {surname}".strip()

                # Find the role for this specific event
                event_ref_list = person.get("event_ref_list", [])
                role = "Unknown"
                for event_ref in event_ref_list:
                    if event_ref.get("ref") == handle:
                        role = event_ref.get("role", "Unknown")
                        break

                # Set primary person name for first line
                if role == "Primary" and not primary_person_name:
                    primary_person_name = full_name

                # Add to participants list
                participants.append(f"{role} ({person_gramps_id})")

        # Check for family backlinks (family events like marriage, divorce)
        if "family" in backlinks:
            families = backlinks["family"]
            family_participants = []

            for family in families:
                family.get("gramps_id", "")

                # Get father and mother from family
                father_handle = family.get("father_handle", "")
                mother_handle = family.get("mother_handle", "")

                # Process father
                if father_handle:
                    try:
                        father_data = await client.make_api_call(
                            api_call=ApiCalls.GET_PERSON,
                            tree_id=tree_id,
                            handle=father_handle,
                        )
                        if father_data:
                            father_gramps_id = father_data.get("gramps_id", "")
                            father_name = father_data.get("primary_name", {})
                            first_name = father_name.get("first_name", "")
                            surname_list = father_name.get("surname_list", [])
                            surname = (
                                surname_list[0].get("surname", "")
                                if surname_list
                                else ""
                            )
                            full_name = f"{first_name} {surname}".strip()

                            family_participants.append(full_name)
                            participants.append(f"Husband ({father_gramps_id})")
                    except Exception:
                        continue

                # Process mother
                if mother_handle:
                    try:
                        mother_data = await client.make_api_call(
                            api_call=ApiCalls.GET_PERSON,
                            tree_id=tree_id,
                            handle=mother_handle,
                        )
                        if mother_data:
                            mother_gramps_id = mother_data.get("gramps_id", "")
                            mother_name = mother_data.get("primary_name", {})
                            first_name = mother_name.get("first_name", "")
                            surname_list = mother_name.get("surname_list", [])
                            surname = (
                                surname_list[0].get("surname", "")
                                if surname_list
                                else ""
                            )
                            full_name = f"{first_name} {surname}".strip()

                            family_participants.append(full_name)
                            participants.append(f"Wife ({mother_gramps_id})")
                    except Exception:
                        continue

            # For family events, show both spouses in the title
            if family_participants:
                primary_person_name = " & ".join(family_participants)

        # First line: Event Type: Primary person's name - gramps_id - [handle]
        first_line = f"{event_type}: {primary_person_name} - {gramps_id} - [{handle}]"
        result = first_line

        # Second line: date - place
        date_place_parts = []
        if event_date and event_date != "date unknown":
            date_place_parts.append(event_date)
        if event_place and event_place != "place unknown":
            date_place_parts.append(event_place)

        if date_place_parts:
            result += f"\n{' - '.join(date_place_parts)}"

        # Third line: participants: role (gramps_id), role (gramps_id)
        if participants:
            result += f"\nParticipants: {', '.join(participants)}"

        # Attached citations: gramps_id(s)
        if citation_list:
            citation_ids = []
            for citation_ref in citation_list:
                citation_handle = (
                    citation_ref
                    if isinstance(citation_ref, str)
                    else citation_ref.get("ref", "")
                )
                if citation_handle:
                    try:
                        citation_data = await client.make_api_call(
                            api_call=ApiCalls.GET_CITATION,
                            tree_id=tree_id,
                            handle=citation_handle,
                        )
                        if citation_data:
                            citation_gramps_id = citation_data.get("gramps_id", "")
                            if citation_gramps_id:
                                citation_ids.append(citation_gramps_id)
                    except Exception:
                        continue

            if citation_ids:
                result += f"\nAttached citations: {', '.join(citation_ids)}"

        # Attached notes: gramps_id(s)
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
                result += f"\nAttached notes: {', '.join(note_ids)}"

        return result + "\n\n"

    except Exception as e:
        logger.debug(f"Failed to format event {handle}: {e}")
        if event_label:
            return None  # For inline use
        return f"• **Event {handle}**\n  Error formatting event: {str(e)}\n\n"
