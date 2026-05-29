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
Minimal GQL (Gramps Query Language) filter for the direct backend.

Supported subset:
  - Property paths with dot notation:  primary_name.first_name
  - Array indexing:                    surname_list[0].surname
  - .length pseudo-property:           media_list.length > 0
  - Operators: =  !=  ~  !~  >  >=  <  <=
  - Conjunctions: and / or  (and binds tighter than or)
  - Boolean (no operator):             media_list  (truthy check)

Unsupported features (any, all, get_person, get_place, …) are treated as
non-matching so the expression returns False for those sub-terms. This is
conservative but safe: users see fewer results rather than wrong ones.
"""

import re
from typing import Any, Dict, Optional


def gql_match(obj: Dict, gql: str) -> bool:
    """
    Return True if *obj* matches the GQL filter expression.

    Supports a subset of the Gramps Query Language:

    - Dot-path property access: ``primary_name.first_name``
    - Array indexing: ``surname_list[0].surname``
    - ``.length`` pseudo-property: ``media_list.length > 0``
    - Operators: ``=``  ``!=``  ``~``  ``!~``  ``>``  ``>=``  ``<``  ``<=``
    - Conjunctions: ``and`` / ``or``  (``and`` binds tighter)
    - Boolean truthy check (no operator): ``media_list``

    Unsupported pseudo-properties (``any``, ``all``, ``get_*``) evaluate to
    ``False`` rather than raising an error.

    Args:
        obj: The Gramps object dict to test (person, family, event, …).
        gql: GQL filter expression string.

    Returns:
        True if the expression matches, False otherwise.
    """
    gql = gql.strip()
    if not gql:
        return True
    return _or_expr(obj, gql)


# ---------------------------------------------------------------------------
# Expression evaluation
# ---------------------------------------------------------------------------

def _or_expr(obj: Dict, expr: str) -> bool:
    # Require whitespace on both sides so bare values like "type = or" are not split.
    parts = re.split(r"\s+or\s+", expr, flags=re.IGNORECASE)
    return any(_and_expr(obj, p.strip()) for p in parts if p.strip())


def _and_expr(obj: Dict, expr: str) -> bool:
    parts = re.split(r"\s+and\s+", expr, flags=re.IGNORECASE)
    return all(_single(obj, p.strip()) for p in parts if p.strip())


# Operators ordered longest-first to avoid partial matches (>= before >)
_OPS = [
    ("!~", lambda a, b: b.lower() not in str(a).lower()),
    ("~",  lambda a, b: b.lower() in str(a).lower()),
    (">=", lambda a, b: _cmp(a) >= _cmp(b)),
    ("<=", lambda a, b: _cmp(a) <= _cmp(b)),
    ("!=", lambda a, b: str(a) != str(b)),
    (">",  lambda a, b: _cmp(a) > _cmp(b)),
    ("<",  lambda a, b: _cmp(a) < _cmp(b)),
    ("=",  lambda a, b: str(a) == str(b)),
]


def _single(obj: Dict, expr: str) -> bool:
    """Evaluate one predicate (no and/or)."""
    expr = expr.strip()
    # Strip at most one layer of matched outer parentheses.
    # Using strip("()") would also eat parens that are part of a value.
    if expr.startswith("(") and expr.endswith(")"):
        expr = expr[1:-1].strip()

    for op, fn in _OPS:
        if op in expr:
            prop, _, val = expr.partition(op)
            val = val.strip().strip("'\"")
            resolved = _resolve(obj, prop.strip())
            if resolved is None:
                return False
            try:
                return fn(resolved, val)
            except (TypeError, ValueError):
                return False

    # No operator → boolean truthiness of the property value
    resolved = _resolve(obj, expr)
    return bool(resolved)


# ---------------------------------------------------------------------------
# Property path resolution
# ---------------------------------------------------------------------------

# Traversal pseudo-properties we cannot follow without the full DB
_SKIP = frozenset({"any", "all"})
_GET_RE = re.compile(r"^get_\w+$")


def _resolve(obj: Any, path: str) -> Optional[Any]:
    """Walk a dot-separated path; return None if any step fails."""
    current = obj
    for part in path.split("."):
        if current is None:
            return None

        # .length pseudo-property
        if part == "length":
            if isinstance(current, (list, str, dict)):
                return len(current)
            return 0

        # Unsupported traversal pseudo-properties
        if part in _SKIP or _GET_RE.match(part):
            return None

        # Array index e.g.  surname_list[0]
        m = re.fullmatch(r"(\w+)\[(\d+)\]", part)
        if m:
            key, idx = m.group(1), int(m.group(2))
            arr = current.get(key, []) if isinstance(current, dict) else None
            if isinstance(arr, list) and idx < len(arr):
                current = arr[idx]
            else:
                return None
        else:
            current = current.get(part) if isinstance(current, dict) else None

    return current


# ---------------------------------------------------------------------------
# Type coercion for comparison operators
# ---------------------------------------------------------------------------

def _cmp(val: Any) -> Any:
    """Coerce *val* to int/float/str for inequality comparisons."""
    try:
        return int(val)
    except (ValueError, TypeError):
        try:
            return float(val)
        except (ValueError, TypeError):
            return str(val)
