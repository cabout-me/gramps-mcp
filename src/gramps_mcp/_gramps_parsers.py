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
XML helper functions and Gramps object parsers.

Pure functions: each converts an xml.etree.ElementTree.Element to a plain
dict matching the structure expected by Gramps Web API responses.
No IO, no side effects, no external dependencies beyond the stdlib.
"""

from typing import Dict

# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------


def _tag(el) -> str:
    """Strip namespace from an element tag."""
    t = el.tag
    return t.split("}", 1)[1] if "}" in t else t


def _text(el, child_tag: str, default: str = "") -> str:
    """Get stripped text of a named child element."""
    for c in el:
        if _tag(c) == child_tag:
            return c.text.strip() if c.text else default
    return default


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

_QUALITY = {"estimated": 1, "calculated": 2}
_MODIFIER = {"before": 1, "after": 2, "about": 3}


def _split_date(val: str):
    """Parse 'YYYY-MM-DD', 'YYYY-MM', or 'YYYY' → (year, month, day)."""
    parts = val.split("-") if val else []
    try:
        y = int(parts[0]) if len(parts) > 0 else 0
        m = int(parts[1]) if len(parts) > 1 else 0
        d = int(parts[2]) if len(parts) > 2 else 0
        return y, m, d
    except (ValueError, IndexError):
        return 0, 0, 0


def _parse_date(el) -> Dict:
    """Convert a dateval/daterange/datespan/datestr element to a date dict.

    The dict matches what format_date() in date_handler.py expects:
      dateval: [day, month, year, False]   (month is 1-indexed)
      modifier: int (0=regular, 1=before, 2=after, 3=about, 4=between, 5=span)
      quality: int (0=regular, 1=estimated, 2=calculated)
      string: str (pre-formatted fallback or empty)
    """
    t = _tag(el)

    if t == "dateval":
        y, m, d = _split_date(el.get("val", ""))
        return {
            "dateval": [d, m, y, False],
            "modifier": _MODIFIER.get(el.get("type", ""), 0),
            "quality": _QUALITY.get(el.get("quality", ""), 0),
            "string": "",
        }

    if t == "daterange":
        start, stop = el.get("start", ""), el.get("stop", "")
        y, m, d = _split_date(start)
        return {
            "dateval": [d, m, y, False],
            "modifier": 4,  # between
            "quality": _QUALITY.get(el.get("quality", ""), 0),
            "string": f"between {start} and {stop}" if start else "",
        }

    if t == "datespan":
        start, stop = el.get("start", ""), el.get("stop", "")
        y, m, d = _split_date(start)
        return {
            "dateval": [d, m, y, False],
            "modifier": 5,  # from...to
            "quality": _QUALITY.get(el.get("quality", ""), 0),
            "string": f"from {start} to {stop}" if start else "",
        }

    if t == "datestr":
        return {
            "dateval": [],
            "modifier": 6,  # text only
            "quality": 0,
            "string": el.get("val", ""),
        }

    return {}


def _find_date(el) -> Dict:
    """Return the first date child of el, or {}."""
    for c in el:
        if _tag(c) in ("dateval", "daterange", "datespan", "datestr"):
            return _parse_date(c)
    return {}


# ---------------------------------------------------------------------------
# Object parsers  (XML element → plain dict matching Web API format)
# ---------------------------------------------------------------------------


def _parse_name(name_el) -> Dict:
    """
    Parse a ``<name>`` element into a primary_name dict.

    Args:
        name_el: ``<name>`` XML element.

    Returns:
        Dict with keys: ``first_name``, ``surname_list``, ``suffix``,
        ``title``, ``call``, ``nick``, ``type``.
    """
    children = {_tag(c): c for c in name_el}

    # Build surname_list from all <surname> children (Gramps 1.7+ allows multiple
    # for compound/patronymic names). Fall back to <last> for older files.
    # Note: must use 'is not None' — xml.etree elements are falsy when childless
    surname_els = [c for c in name_el if _tag(c) == "surname"]
    if surname_els:
        surname_list = [
            {
                "surname": s.text.strip() if s.text else "",
                "primary": i == 0,
                "prefix": "",
                "connector": "",
            }
            for i, s in enumerate(surname_els)
        ]
    else:
        last_el = children.get("last")
        last = last_el.text.strip() if last_el is not None and last_el.text else ""
        surname_list = [
            {"surname": last, "primary": True, "prefix": "", "connector": ""}
        ]

    fn_el = children.get("first")
    first = fn_el.text.strip() if fn_el is not None and fn_el.text else ""

    suffix_el = children.get("suffix")
    suffix = suffix_el.text.strip() if suffix_el is not None and suffix_el.text else ""

    call_el = children.get("call")
    call = call_el.text.strip() if call_el is not None and call_el.text else ""

    nick_el = children.get("nick")
    nick = nick_el.text.strip() if nick_el is not None and nick_el.text else ""

    title_el = children.get("title")
    title = title_el.text.strip() if title_el is not None and title_el.text else ""

    return {
        "first_name": first,
        "surname_list": surname_list,
        "suffix": suffix,
        "title": title,
        "call": call,
        "nick": nick,
        "type": name_el.get("type", "Birth Name"),
    }


def _parse_address(el) -> Dict:
    """
    Parse an ``<address>`` element to an address dict.

    Args:
        el: ``<address>`` XML element.

    Returns:
        Dict with keys: ``street``, ``locality``, ``city``, ``county``,
        ``state``, ``country``, ``postal``, ``phone``, ``date``, ``note_list``.
    """
    return {
        "street": _text(el, "street"),
        "locality": _text(el, "locality"),
        "city": _text(el, "city"),
        "county": _text(el, "county"),
        "state": _text(el, "state"),
        "country": _text(el, "country"),
        "postal": _text(el, "postal"),
        "phone": _text(el, "phone"),
        "date": _find_date(el),
        "note_list": [c.get("hlink", "") for c in el if _tag(c) == "noteref"],
    }


def _parse_person(el, events_by_handle: Dict) -> Dict:
    """
    Convert a ``<person>`` element to a Web API-compatible dict.

    Args:
        el: ``<person>`` XML element.
        events_by_handle: Pre-built event index keyed by handle, used to
            resolve ``birth_ref_index`` and ``death_ref_index``.

    Returns:
        Dict with keys: ``handle``, ``gramps_id``, ``change``, ``gender``,
        ``primary_name``, ``birth_ref_index``, ``death_ref_index``,
        ``event_ref_list``, ``family_list``, ``parent_family_list``,
        ``note_list``, ``citation_list``, ``media_list``, ``urls``,
        ``address_list``.
    """
    handle = el.get("handle", "")
    gramps_id = el.get("id", "")

    # Gender (M/F/U → 1/0/2)
    gender_map = {"M": 1, "F": 0, "U": 2}
    gender = gender_map.get(_text(el, "gender"), 2)

    # Primary name: prefer Birth Name, then first available
    name_els = [c for c in el if _tag(c) == "name"]
    birth_name_types = ("Birth Name", "Geburtsname", "")
    birth_names = [n for n in name_els if n.get("type", "") in birth_name_types]
    name_el = birth_names[0] if birth_names else (name_els[0] if name_els else None)
    primary_name = _parse_name(name_el) if name_el is not None else {
        "first_name": "",
        "surname_list": [
            {"surname": "", "primary": True, "prefix": "", "connector": ""}
        ],
    }

    # Event refs (preserve order — used for birth/death index)
    event_refs = [c for c in el if _tag(c) == "eventref"]
    event_ref_list = [
        {"ref": c.get("hlink", ""), "role": c.get("role", "")} for c in event_refs
    ]

    # Birth and death ref indices — look up event types from the pre-built index
    birth_ref_index = -1
    death_ref_index = -1
    for i, eref in enumerate(event_ref_list):
        etype = events_by_handle.get(eref["ref"], {}).get("type", "")
        if birth_ref_index == -1 and etype == "Birth":
            birth_ref_index = i
        if death_ref_index == -1 and etype in ("Death", "Burial", "Cremation"):
            death_ref_index = i

    # Family links
    parentin = [c.get("hlink", "") for c in el if _tag(c) == "parentin"]
    childof = [c.get("hlink", "") for c in el if _tag(c) == "childof"]

    # Attached objects
    note_list = [c.get("hlink", "") for c in el if _tag(c) == "noteref"]
    citation_list = [c.get("hlink", "") for c in el if _tag(c) == "citationref"]
    # DTD: objref* — media object references (tag is <objref>, not <mediaref>)
    media_list = [{"ref": c.get("hlink", "")} for c in el if _tag(c) == "objref"]

    urls = []
    for u in [c for c in el if _tag(c) == "url"]:
        urls.append(
            {
                "path": u.get("href", ""),
                "description": u.get("description", ""),
                "type": u.get("type", ""),
            }
        )

    address_list = [_parse_address(c) for c in el if _tag(c) == "address"]

    return {
        "gramps_id": gramps_id,
        "handle": handle,
        "change": int(el.get("change", "0") or "0"),
        "gender": gender,
        "primary_name": primary_name,
        "birth_ref_index": birth_ref_index,
        "death_ref_index": death_ref_index,
        "event_ref_list": event_ref_list,
        "family_list": parentin,        # families where this person is spouse/parent
        "parent_family_list": childof,  # families where this person is a child
        "note_list": note_list,
        "citation_list": citation_list,
        "media_list": media_list,
        "urls": urls,
        "address_list": address_list,
    }


def _parse_event(el) -> Dict:
    """
    Convert an ``<event>`` element to a Web API-compatible dict.

    Args:
        el: ``<event>`` XML element.

    Returns:
        Dict with keys: ``handle``, ``gramps_id``, ``change``, ``type``,
        ``date``, ``place``, ``description``, ``note_list``, ``citation_list``.
    """
    handle = el.get("handle", "")
    gramps_id = el.get("id", "")

    event_type = _text(el, "type")
    description = _text(el, "description")
    date = _find_date(el)

    place_el = next((c for c in el if _tag(c) == "place"), None)
    place = place_el.get("hlink", "") if place_el is not None else ""

    return {
        "gramps_id": gramps_id,
        "handle": handle,
        "change": int(el.get("change", "0") or "0"),
        "type": event_type,
        "date": date,
        "place": place,
        "description": description,
        "note_list": [c.get("hlink", "") for c in el if _tag(c) == "noteref"],
        "citation_list": [c.get("hlink", "") for c in el if _tag(c) == "citationref"],
    }


def _parse_family(el) -> Dict:
    """
    Convert a ``<family>`` element to a Web API-compatible dict.

    Args:
        el: ``<family>`` XML element.

    Returns:
        Dict with keys: ``handle``, ``gramps_id``, ``change``,
        ``father_handle``, ``mother_handle``, ``child_ref_list``,
        ``event_ref_list``, ``relationship``, ``note_list``,
        ``citation_list``, ``media_list``.
    """
    handle = el.get("handle", "")
    gramps_id = el.get("id", "")

    rel_el = next((c for c in el if _tag(c) == "rel"), None)
    relationship = rel_el.get("type", "Married") if rel_el is not None else "Married"

    father_el = next((c for c in el if _tag(c) == "father"), None)
    mother_el = next((c for c in el if _tag(c) == "mother"), None)
    father_handle = father_el.get("hlink", "") if father_el is not None else ""
    mother_handle = mother_el.get("hlink", "") if mother_el is not None else ""

    child_ref_list = [
        {
            "ref": c.get("hlink", ""),
            "frel": c.get("frel", "Birth"),
            "mrel": c.get("mrel", "Birth"),
        }
        for c in el
        if _tag(c) == "childref"
    ]

    event_ref_list = [
        {"ref": c.get("hlink", ""), "role": c.get("role", "")}
        for c in el
        if _tag(c) == "eventref"
    ]

    return {
        "gramps_id": gramps_id,
        "handle": handle,
        "change": int(el.get("change", "0") or "0"),
        "father_handle": father_handle,
        "mother_handle": mother_handle,
        "child_ref_list": child_ref_list,
        "event_ref_list": event_ref_list,
        "relationship": relationship,
        "note_list": [c.get("hlink", "") for c in el if _tag(c) == "noteref"],
        "citation_list": [c.get("hlink", "") for c in el if _tag(c) == "citationref"],
        "media_list": [{"ref": c.get("hlink", "")} for c in el if _tag(c) == "objref"],
    }
