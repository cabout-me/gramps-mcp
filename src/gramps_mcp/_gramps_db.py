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
Gramps database loader and in-memory store.

Reads .gpkg / .gramps files and builds a GrampsXmlDB — a dict-based
in-memory store with handle and Gramps-ID lookups.
"""

import gzip
import logging
import os
import re
import shutil
import tarfile
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from ._gramps_parsers import (
    _parse_event,
    _parse_family,
    _parse_person,
    _tag,
)
from ._gramps_parsers_ext import (
    _parse_citation,
    _parse_media,
    _parse_note,
    _parse_place,
    _parse_repository,
    _parse_source,
)
from .client import GrampsAPIError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Database loader — .gpkg / .gramps → in-memory indices
# ---------------------------------------------------------------------------


def _open_gramps_content(path: str) -> bytes:
    """Read a .gramps file, which may be gzip-compressed or plain XML."""
    with open(path, "rb") as f:
        magic = f.read(2)

    if magic == b"\x1f\x8b":
        with gzip.open(path, "rb") as f:
            return f.read()

    with open(path, "rb") as f:
        return f.read()


def _load_gpkg(path: str) -> "GrampsXmlDB":
    """Load a .gpkg or .gramps file into an in-memory GrampsXmlDB."""
    if path.lower().endswith(".gpkg"):
        tmp_dir = _extract_gpkg(path)
        try:
            gramps_file = _find_gramps_file(tmp_dir)
            content = _open_gramps_content(gramps_file)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
    elif path.lower().endswith(".gramps"):
        content = _open_gramps_content(path)
    else:
        raise GrampsAPIError(
            f"Unsupported file type: '{path}'. "
            "GRAMPS_DB_PATH must point to a .gpkg or .gramps file."
        )
    return _parse_xml(content, source_name=os.path.basename(path))


def _extract_gpkg(gpkg_path: str) -> str:
    """Extract a .gpkg archive to a temp dir and return the dir path."""
    import tempfile
    tmp_dir = tempfile.mkdtemp(prefix="gramps_mcp_")
    try:
        with tarfile.open(gpkg_path, "r:gz") as tar:
            tar.extractall(tmp_dir, filter="data")
        logger.info("Extracted .gpkg to %s", tmp_dir)
        return tmp_dir
    except Exception as exc:
        raise GrampsAPIError(f"Cannot extract '{gpkg_path}': {exc}") from exc


def _find_gramps_file(directory: str) -> str:
    """Find the .gramps XML file inside an extracted archive directory."""
    for name in os.listdir(directory):
        if name.endswith(".gramps"):
            return os.path.join(directory, name)
    raise GrampsAPIError(
        f"No .gramps file found in '{directory}'. The .gpkg may be corrupt."
    )


def _parse_xml(content: bytes, source_name: str) -> "GrampsXmlDB":
    """Parse Gramps XML content into a GrampsXmlDB."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise GrampsAPIError(f"XML parse error in '{source_name}': {exc}") from exc

    # Index XML sections by (namespace-stripped) tag
    sections: Dict[str, Any] = {}
    for child in root:
        sections[_tag(child)] = child

    # --- Step 1: parse events first (needed for person birth/death indices) ---
    events: Dict[str, Dict] = {}
    events_section = sections.get("events")
    if events_section is not None:
        for el in events_section:
            if _tag(el) == "event":
                obj = _parse_event(el)
                events[obj["handle"]] = obj

    # --- Step 2: parse people (need events index) ---
    people: Dict[str, Dict] = {}
    people_section = sections.get("people")
    if people_section is not None:
        for el in people_section:
            if _tag(el) == "person":
                obj = _parse_person(el, events)
                people[obj["handle"]] = obj

    # --- Step 3: parse remaining types ---
    def _parse_section(section_tag: str, element_tag: str, parser) -> Dict[str, Dict]:
        result: Dict[str, Dict] = {}
        section = sections.get(section_tag)
        if section is not None:
            for el in section:
                if _tag(el) == element_tag:
                    obj = parser(el)
                    result[obj["handle"]] = obj
        return result

    families = _parse_section("families", "family", _parse_family)
    places = _parse_section("places", "placeobj", _parse_place)
    sources = _parse_section("sources", "source", _parse_source)
    citations = _parse_section("citations", "citation", _parse_citation)
    notes = _parse_section("notes", "note", _parse_note)
    media = _parse_section("objects", "object", _parse_media)
    repositories = _parse_section("repositories", "repository", _parse_repository)

    logger.info(
        "Loaded '%s': %d people, %d families, %d events, %d places, "
        "%d sources, %d citations, %d notes, %d media, %d repositories",
        source_name,
        len(people), len(families), len(events), len(places),
        len(sources), len(citations), len(notes), len(media), len(repositories),
    )

    return GrampsXmlDB(
        source_name=source_name,
        people=people,
        families=families,
        events=events,
        places=places,
        sources=sources,
        citations=citations,
        notes=notes,
        media=media,
        repositories=repositories,
    )


# ---------------------------------------------------------------------------
# Report formatting helpers
# ---------------------------------------------------------------------------


def _name_parts(person: Dict) -> tuple:
    """Return (first_name, surname) for a person dict."""
    pn = person.get("primary_name", {})
    first = pn.get("first_name", "")
    sl = pn.get("surname_list", [])
    surname = sl[0].get("surname", "") if sl else ""
    return first, surname


def _year_from_date(date: Dict) -> str:
    """Extract a 4-digit year string from a parsed date dict, or ''."""
    dv = date.get("dateval", [])
    if len(dv) >= 3 and dv[2]:
        return str(dv[2])
    s = date.get("string", "")
    m = re.search(r"\b(\d{4})\b", s)
    return m.group(1) if m else ""


def _full_name(person: Dict) -> str:
    """Return 'First Surname' for a person dict."""
    pn = person.get("primary_name", {})
    first = pn.get("first_name", "")
    surnames = " ".join(s.get("surname", "") for s in pn.get("surname_list", []))
    return f"{first} {surnames}".strip() or "Unknown"


def _person_summary(person: Dict, events: Dict[str, Dict]) -> str:
    """Format a person as an HTML fragment with name, ID, and vital years."""
    name = _full_name(person)
    gid = person.get("gramps_id", "")
    event_refs = person.get("event_ref_list", [])

    birth_year = ""
    bi = person.get("birth_ref_index", -1)
    if 0 <= bi < len(event_refs):
        ev = events.get(event_refs[bi]["ref"])
        if ev:
            birth_year = _year_from_date(ev.get("date", {}))

    death_year = ""
    di = person.get("death_ref_index", -1)
    if 0 <= di < len(event_refs):
        ev = events.get(event_refs[di]["ref"])
        if ev:
            death_year = _year_from_date(ev.get("date", {}))

    parts = [f"<strong>{name}</strong> ({gid})"]
    if birth_year:
        parts.append(f"* {birth_year}")
    if death_year:
        parts.append(f"&#8224; {death_year}")
    return " &#8212; ".join(parts)


# ---------------------------------------------------------------------------
# In-memory database
# ---------------------------------------------------------------------------


class GrampsXmlDB:
    """In-memory Gramps database built from parsed XML."""

    def __init__(
        self,
        source_name: str,
        people: Dict[str, Dict],
        families: Dict[str, Dict],
        events: Dict[str, Dict],
        places: Dict[str, Dict],
        sources: Dict[str, Dict],
        citations: Dict[str, Dict],
        notes: Dict[str, Dict],
        media: Dict[str, Dict],
        repositories: Dict[str, Dict],
    ):
        self.source_name = source_name
        self.people = people
        self.families = families
        self.events = events
        self.places = places
        self.sources = sources
        self.citations = citations
        self.notes = notes
        self.media = media
        self.repositories = repositories

    def _store(self, obj_type: str) -> Dict[str, Dict]:
        return {
            "person": self.people,
            "family": self.families,
            "event": self.events,
            "place": self.places,
            "source": self.sources,
            "citation": self.citations,
            "note": self.notes,
            "media": self.media,
            "repository": self.repositories,
        }[obj_type]

    def get(self, obj_type: str, handle: str) -> Optional[Dict]:
        return self._store(obj_type).get(handle)

    def get_by_id(self, obj_type: str, gramps_id: str) -> Optional[Dict]:
        for obj in self._store(obj_type).values():
            if obj.get("gramps_id") == gramps_id:
                return obj
        return None

    def all(self, obj_type: str) -> List[Dict]:
        return list(self._store(obj_type).values())

    def count(self, obj_type: str) -> int:
        return len(self._store(obj_type))

    def build_extended_person(self, person: Dict) -> Dict:
        """Build the 'extended' block for a person (events + families)."""
        events = []
        for eref in person.get("event_ref_list", []):
            ev = self.events.get(eref.get("ref", ""))
            if ev:
                events.append(ev)

        families = []
        for fh in person.get("family_list", []):
            fam = self.families.get(fh)
            if fam:
                families.append(fam)

        parent_families = []
        for fh in person.get("parent_family_list", []):
            fam = self.families.get(fh)
            if fam:
                parent_families.append(fam)

        return {
            "events": events,
            "families": families,
            "parent_families": parent_families,
        }

    # ------------------------------------------------------------------
    # Timelines
    # ------------------------------------------------------------------

    def _timeline_item(self, event: Dict, role: str, person_info: Dict) -> Dict:
        """Build a single timeline item dict from an event."""
        place_handle = event.get("place", "")
        place = self.places.get(place_handle) if place_handle else None
        display_name = place.get("title", "") if place else ""
        year = _year_from_date(event.get("date", {}))
        return {
            "type": event.get("type", ""),
            "gramps_id": event.get("gramps_id", ""),
            "role": role,
            "handle": event.get("handle", ""),
            "place": {"display_name": display_name},
            "person": person_info,
            "date": year,
        }

    def build_person_timeline(self, handle: str) -> List[Dict]:
        """
        Build a timeline for a person, sorted ascending by year.

        Includes the person's own events (role from the event ref) and events
        from families where the person is a spouse/parent (role ``Family``).
        Each item carries a ``person`` sub-dict with ``relationship``,
        ``name_given``, ``name_surname``, and ``gramps_id`` so the detail
        handler can display participant context.

        Args:
            handle: Internal handle of the person.

        Returns:
            List of timeline item dicts ordered by year ascending.  Each dict
            has keys: ``type``, ``gramps_id``, ``role``, ``handle``,
            ``place`` (with ``display_name``), ``person``, ``date`` (year str).

        Raises:
            GrampsAPIError: If no person with the given handle exists.
        """
        person = self.people.get(handle)
        if person is None:
            raise GrampsAPIError(f"person with handle '{handle}' not found")

        first, surname = _name_parts(person)
        self_info = {
            "relationship": "self",
            "name_given": first,
            "name_surname": surname,
            "gramps_id": person.get("gramps_id", ""),
        }

        items: List[Dict] = []

        for eref in person.get("event_ref_list", []):
            ev = self.events.get(eref.get("ref", ""))
            if ev:
                items.append(
                    self._timeline_item(ev, eref.get("role", "Primary"), self_info)
                )

        for fh in person.get("family_list", []):
            fam = self.families.get(fh)
            if not fam:
                continue
            if fam.get("father_handle") == handle:
                spouse = self.people.get(fam.get("mother_handle", ""))
            else:
                spouse = self.people.get(fam.get("father_handle", ""))
            if spouse:
                sf, ss = _name_parts(spouse)
                spouse_info: Dict = {
                    "relationship": "spouse",
                    "name_given": sf,
                    "name_surname": ss,
                    "gramps_id": spouse.get("gramps_id", ""),
                }
            else:
                spouse_info = {}
            for eref in fam.get("event_ref_list", []):
                ev = self.events.get(eref.get("ref", ""))
                if ev:
                    items.append(
                        self._timeline_item(ev, eref.get("role", "Family"), spouse_info)
                    )

        items.sort(key=lambda x: int(x["date"]) if x["date"].isdigit() else 0)
        return items

    def build_family_timeline(self, handle: str) -> List[Dict]:
        """
        Build a timeline for a family, sorted ascending by year.

        Includes the family's own events and the individual events of both
        parents (father and mother).  Each parent event carries a ``person``
        sub-dict with ``relationship`` (``father`` or ``mother``), name parts,
        and ``gramps_id``.

        Args:
            handle: Internal handle of the family.

        Returns:
            List of timeline item dicts ordered by year ascending.  Same
            structure as :meth:`build_person_timeline`.

        Raises:
            GrampsAPIError: If no family with the given handle exists.
        """
        fam = self.families.get(handle)
        if fam is None:
            raise GrampsAPIError(f"family with handle '{handle}' not found")

        items: List[Dict] = []

        for eref in fam.get("event_ref_list", []):
            ev = self.events.get(eref.get("ref", ""))
            if ev:
                items.append(self._timeline_item(ev, eref.get("role", "Family"), {}))

        for role_key, rel_str in (
            ("father_handle", "father"),
            ("mother_handle", "mother"),
        ):
            parent = self.people.get(fam.get(role_key, ""))
            if not parent:
                continue
            pf, ps = _name_parts(parent)
            pinfo = {
                "relationship": rel_str,
                "name_given": pf,
                "name_surname": ps,
                "gramps_id": parent.get("gramps_id", ""),
            }
            for eref in parent.get("event_ref_list", []):
                ev = self.events.get(eref.get("ref", ""))
                if ev:
                    items.append(
                        self._timeline_item(ev, eref.get("role", "Primary"), pinfo)
                    )

        items.sort(key=lambda x: int(x["date"]) if x["date"].isdigit() else 0)
        return items

    def build_extended_family(self, family: Dict) -> Dict:
        """Build the 'extended' block for a family (events + members)."""
        events = []
        for eref in family.get("event_ref_list", []):
            ev = self.events.get(eref.get("ref", ""))
            if ev:
                events.append(ev)

        father = self.people.get(family.get("father_handle", ""))
        mother = self.people.get(family.get("mother_handle", ""))

        children = []
        for cref in family.get("child_ref_list", []):
            child = self.people.get(cref.get("ref", ""))
            if child:
                children.append(child)

        return {
            "events": events,
            "father": father,
            "mother": mother,
            "children": children,
        }

    # ------------------------------------------------------------------
    # BFS traversal (shared by GrampsDirectClient and GrampsSqliteClient)
    # ------------------------------------------------------------------

    def traverse_ancestors(self, start: Dict, max_gen: int) -> str:
        """BFS up the family tree; return HTML for html_to_markdown."""
        name = _full_name(start)
        gid = start["gramps_id"]
        html = [f"<h1>Ancestors of {name} ({gid})</h1>"]
        labels = {1: "Parents", 2: "Grandparents", 3: "Great-grandparents"}
        seen = {start["handle"]}
        queue = [start]

        for gen in range(1, max_gen + 1):
            next_level: List[Dict] = []
            items: List[str] = []
            for person in queue:
                for fh in person.get("parent_family_list", []):
                    fam = self.families.get(fh)
                    if not fam:
                        continue
                    for role in ("father_handle", "mother_handle"):
                        h = fam.get(role, "")
                        if h and h not in seen:
                            p = self.people.get(h)
                            if p:
                                seen.add(h)
                                next_level.append(p)
                                items.append(
                                    f"<li>{_person_summary(p, self.events)}</li>"
                                )
            if not items:
                break
            label = labels.get(gen, f"Generation +{gen}")
            html.append(
                f"<h2>Generation {gen} &#8212; {label}</h2>"
                f"<ul>{''.join(items)}</ul>"
            )
            queue = next_level

        if len(html) == 1:
            html.append("<p>No ancestors found in the database.</p>")
        return "\n".join(html)

    def traverse_descendants(self, start: Dict, max_gen: int) -> str:
        """BFS down the family tree; return HTML for html_to_markdown."""
        name = _full_name(start)
        gid = start["gramps_id"]
        html = [f"<h1>Descendants of {name} ({gid})</h1>"]
        labels = {1: "Children", 2: "Grandchildren", 3: "Great-grandchildren"}
        seen = {start["handle"]}
        queue = [start]

        for gen in range(1, max_gen + 1):
            next_level: List[Dict] = []
            items: List[str] = []
            for person in queue:
                for fh in person.get("family_list", []):
                    fam = self.families.get(fh)
                    if not fam:
                        continue
                    for cref in fam.get("child_ref_list", []):
                        h = cref.get("ref", "")
                        if h and h not in seen:
                            child = self.people.get(h)
                            if child:
                                seen.add(h)
                                next_level.append(child)
                                s = _person_summary(child, self.events)
                                items.append(f"<li>{s}</li>")
            if not items:
                break
            label = labels.get(gen, f"Generation +{gen}")
            html.append(
                f"<h2>Generation {gen} &#8212; {label}</h2>"
                f"<ul>{''.join(items)}</ul>"
            )
            queue = next_level

        if len(html) == 1:
            html.append("<p>No descendants found in the database.</p>")
        return "\n".join(html)
