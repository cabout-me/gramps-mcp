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
XML parsers for secondary Gramps object types.

Covers: place, source, citation, note, media (object), repository.
Primary object parsers (person, event, family) live in _gramps_parsers.py.
"""

from typing import Dict

from ._gramps_parsers import _find_date, _tag, _text


def _parse_place(el) -> Dict:
    """
    Convert a ``<placeobj>`` element to a Web API-compatible dict.

    Args:
        el: ``<placeobj>`` XML element.

    Returns:
        Dict with keys: ``handle``, ``gramps_id``, ``change``, ``title``,
        ``name`` (with ``value``), ``place_type``, ``placeref_list``, ``urls``.
    """
    handle = el.get("handle", "")
    gramps_id = el.get("id", "")

    ptitle_el = next((c for c in el if _tag(c) == "ptitle"), None)
    pname_el = next((c for c in el if _tag(c) == "pname"), None)

    title = ptitle_el.text.strip() if ptitle_el is not None and ptitle_el.text else ""
    pname_value = pname_el.get("value", "") if pname_el is not None else ""
    display_name = pname_value or title

    placeref_list = [
        {"ref": c.get("hlink", "")} for c in el if _tag(c) == "placeref"
    ]

    return {
        "gramps_id": gramps_id,
        "handle": handle,
        "change": int(el.get("change", "0") or "0"),
        "title": title,
        "name": {"value": display_name},
        "place_type": el.get("type", ""),
        "placeref_list": placeref_list,
        "urls": [
            {
                "path": u.get("href", ""),
                "description": u.get("description", ""),
                "type": u.get("type", ""),
            }
            for u in el
            if _tag(u) == "url"
        ],
    }


def _parse_source(el) -> Dict:
    """
    Convert a ``<source>`` element to a Web API-compatible dict.

    Args:
        el: ``<source>`` XML element.

    Returns:
        Dict with keys: ``handle``, ``gramps_id``, ``change``, ``title``,
        ``author``, ``pubinfo``, ``abbrev``, ``note_list``, ``media_list``,
        ``reporef_list``, ``attribute_list``.
    """
    handle = el.get("handle", "")
    gramps_id = el.get("id", "")

    return {
        "gramps_id": gramps_id,
        "handle": handle,
        "change": int(el.get("change", "0") or "0"),
        "title": _text(el, "stitle"),
        "author": _text(el, "sauthor"),
        "pubinfo": _text(el, "spubinfo"),
        "abbrev": _text(el, "sabbrev"),
        "note_list": [c.get("hlink", "") for c in el if _tag(c) == "noteref"],
        "media_list": [
            {"ref": c.get("hlink", "")} for c in el if _tag(c) == "objref"
        ],
        "reporef_list": [
            {
                "ref": c.get("hlink", ""),
                "callno": c.get("callno", ""),
                "medium": c.get("medium", ""),
            }
            for c in el
            if _tag(c) == "reporef"
        ],
        "attribute_list": [
            {"key": c.get("key", ""), "value": c.get("value", "")}
            for c in el
            if _tag(c) == "data_item"
        ],
    }


def _parse_citation(el) -> Dict:
    """
    Convert a ``<citation>`` element to a Web API-compatible dict.

    Args:
        el: ``<citation>`` XML element.

    Returns:
        Dict with keys: ``handle``, ``gramps_id``, ``change``, ``page``,
        ``confidence``, ``source_handle``, ``date``, ``note_list``.
    """
    handle = el.get("handle", "")
    gramps_id = el.get("id", "")

    page = _text(el, "page")
    confidence_str = _text(el, "confidence")
    confidence = int(confidence_str) if confidence_str.isdigit() else 0

    sourceref_el = next((c for c in el if _tag(c) == "sourceref"), None)
    source_handle = sourceref_el.get("hlink", "") if sourceref_el is not None else ""

    return {
        "gramps_id": gramps_id,
        "handle": handle,
        "change": int(el.get("change", "0") or "0"),
        "page": page,
        "confidence": confidence,
        "source_handle": source_handle,
        "date": _find_date(el),
        "note_list": [c.get("hlink", "") for c in el if _tag(c) == "noteref"],
    }


def _parse_note(el) -> Dict:
    """
    Convert a ``<note>`` element to a Web API-compatible dict.

    Args:
        el: ``<note>`` XML element.

    Returns:
        Dict with keys: ``handle``, ``gramps_id``, ``change``, ``type``,
        ``text`` (with ``string`` key).
    """
    handle = el.get("handle", "")
    gramps_id = el.get("id", "")

    text_el = next((c for c in el if _tag(c) == "text"), None)
    text = text_el.text.strip() if text_el is not None and text_el.text else ""

    return {
        "gramps_id": gramps_id,
        "handle": handle,
        "change": int(el.get("change", "0") or "0"),
        "type": el.get("type", ""),
        "text": {"string": text},
    }


def _parse_media(el) -> Dict:
    """
    Convert an ``<object>`` (media) element to a Web API-compatible dict.

    Args:
        el: ``<object>`` XML element.

    Returns:
        Dict with keys: ``handle``, ``gramps_id``, ``change``, ``path``,
        ``mime``, ``desc``, ``checksum``, ``date``, ``note_list``.
    """
    handle = el.get("handle", "")
    gramps_id = el.get("id", "")

    file_el = next((c for c in el if _tag(c) == "file"), None)
    src = file_el.get("src", "") if file_el is not None else ""
    mime = file_el.get("mime", "") if file_el is not None else ""
    description = file_el.get("description", "") if file_el is not None else ""
    checksum = file_el.get("checksum", "") if file_el is not None else ""

    return {
        "gramps_id": gramps_id,
        "handle": handle,
        "change": int(el.get("change", "0") or "0"),
        "path": src,
        "mime": mime,
        "desc": description,
        "checksum": checksum,
        "date": _find_date(el),
        "note_list": [c.get("hlink", "") for c in el if _tag(c) == "noteref"],
    }


def _parse_repository(el) -> Dict:
    """
    Convert a ``<repository>`` element to a Web API-compatible dict.

    Args:
        el: ``<repository>`` XML element.

    Returns:
        Dict with keys: ``handle``, ``gramps_id``, ``change``, ``name``,
        ``type``, ``urls``, ``note_list``.
    """
    handle = el.get("handle", "")
    gramps_id = el.get("id", "")

    name = _text(el, "rname") or gramps_id
    repo_type = _text(el, "type")

    return {
        "gramps_id": gramps_id,
        "handle": handle,
        "change": int(el.get("change", "0") or "0"),
        "name": name,
        "type": repo_type,
        "urls": [
            {
                "path": u.get("href", ""),
                "description": u.get("description", ""),
                "type": u.get("type", ""),
            }
            for u in el
            if _tag(u) == "url"
        ],
        "note_list": [c.get("hlink", "") for c in el if _tag(c) == "noteref"],
    }
