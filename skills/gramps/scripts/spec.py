#!/usr/bin/env python3
# gramps-mcp - AI-Powered Genealogy Research & Management
# Copyright (C) 2026 cabout.me
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
Expand a schema from the instance's own OpenAPI spec.

Use jq for browsing the spec -- paths, parameters, operations. This script
exists only for the one thing jq is bad at: Gramps schemas are mutually
recursive ($ref cycles), so inlining them needs cycle detection. Fully inlined,
Person is ~59 KB; summarised, 2 KB.

    spec.py --file                     path to the cached spec, for jq
    spec.py Person                     an object's fields, one line each
    spec.py Person.primary_name        drill into a field
    spec.py Person.primary_name --full raw JSON for that fragment
    spec.py --refresh                  re-download before answering

Served unauthenticated at /api/openapi.json, so this works before you have a
token.
"""

import argparse
import json
import sys
import time
import urllib.request

from api import CACHE, config

SPEC_FILE = CACHE / "openapi.json"
MAX_AGE = 24 * 3600


def load(refresh=False):
    """
    Fetch the instance's OpenAPI spec, caching it for a day.

    Args:
        refresh (bool): Ignore any cached copy.

    Returns:
        dict: The parsed spec.
    """
    fresh = SPEC_FILE.is_file() and time.time() - SPEC_FILE.stat().st_mtime < MAX_AGE
    if not refresh and fresh:
        return json.loads(SPEC_FILE.read_text())

    base, _, _ = config()
    with urllib.request.urlopen(f"{base}/openapi.json", timeout=60) as response:
        raw = response.read()
    CACHE.mkdir(parents=True, exist_ok=True, mode=0o700)
    SPEC_FILE.write_bytes(raw)
    return json.loads(raw)


def resolve(node, schemas, seen=()):
    """
    Inline $ref pointers so a schema reads as one document.

    Args:
        node (object): Spec fragment to walk.
        schemas (dict): The spec's components/schemas map.
        seen (tuple): Schema names already inlined on this branch.

    Returns:
        object: The fragment with references replaced.
    """
    if isinstance(node, dict):
        ref = node.get("$ref")
        if ref:
            name = ref.rsplit("/", 1)[-1]
            # Reason: Gramps schemas are mutually recursive (Person -> EventRef
            # -> Event -> ...), so repeats collapse to a name instead of looping.
            if name in seen:
                return f"<{name}>"
            return resolve(schemas.get(name, {}), schemas, seen + (name,))
        return {key: resolve(value, schemas, seen) for key, value in node.items()}
    if isinstance(node, list):
        return [resolve(item, schemas, seen) for item in node]
    return node


def kind(node):
    """Render a schema fragment's type as a short string like 'array[object]'."""
    if isinstance(node, str):
        return node
    for key in ("allOf", "anyOf", "oneOf"):
        if node.get(key):
            return kind(node[key][0])
    if node.get("enum"):
        return "enum"
    declared = node.get("type") or ("object" if "properties" in node else "any")
    if declared == "array":
        return f"array[{kind(node.get('items', {}))}]"
    return declared


def unwrap(node):
    """Strip allOf/anyOf/oneOf and array wrappers to reach the object beneath."""
    while True:
        for key in ("allOf", "anyOf", "oneOf"):
            if node.get(key):
                node = node[key][0]
                break
        else:
            if isinstance(node, dict) and node.get("type") == "array":
                node = node.get("items", {})
                continue
            return node


def dig(schema, path):
    """Follow a dotted property path into a schema, e.g. 'event_ref_list.date'."""
    for part in path:
        properties = unwrap(schema).get("properties", {})
        if part not in properties:
            sys.exit(f"no property {part!r}; available: {sorted(properties)}")
        schema = properties[part]
    return schema


def describe(schema, label):
    """Print one level of a schema: every property with its type and summary."""
    node = unwrap(schema)
    properties = node.get("properties")
    if not properties:
        print(f"{label}: {kind(schema)}")
        if node.get("enum"):
            print("  values: " + ", ".join(str(v) for v in node["enum"]))
        if node.get("description"):
            print(f"  {node['description']}")
        return

    print(f"{label} ({kind(schema)})")
    width = max(len(name) for name in properties)
    nested = []
    for name, value in sorted(properties.items()):
        summary = (value.get("description") or "").split("\n")[0]
        print(f"  {name:<{width}}  {kind(value):<16}  {summary}")
        if unwrap(value).get("properties"):
            nested.append(name)
    if nested:
        print(f"\nexpand: spec.py {label}.<{'|'.join(nested[:6])}>")


def main():
    """Expand one schema, or report where the cached spec lives."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("schema", nargs="?", help="schema name, or Name.field.subfield")
    parser.add_argument("--file", action="store_true", help="print the cache path")
    parser.add_argument("--full", action="store_true", help="raw JSON, no summarising")
    parser.add_argument("--refresh", action="store_true", help="re-download the spec")
    args = parser.parse_args()

    spec = load(args.refresh)
    if args.file or not args.schema:
        print(SPEC_FILE)
        return

    schemas = spec.get("components", {}).get("schemas", {})
    root, *path = args.schema.split(".")
    if root not in schemas:
        close = [n for n in schemas if root.lower() in n.lower()]
        sys.exit(f"no schema {root!r}" + (f"; did you mean {close}?" if close else ""))

    node = dig(resolve(schemas[root], schemas, (root,)), path)
    if args.full:
        print(json.dumps(node, indent=2))
    else:
        describe(node, args.schema)


if __name__ == "__main__":
    main()
