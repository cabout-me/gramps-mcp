#!/usr/bin/env python3
"""
Offline checks for the parts of api.py and spec.py that are not just HTTP.

No network, no credentials, no test framework: python3 selfcheck.py
"""

import base64
import json
import time

from api import _expired
from spec import describe, dig, kind, resolve


def _token(exp):
    """Build a signature-free JWT carrying one exp claim."""
    payload = base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode()).rstrip(b"=")
    return "header." + payload.decode() + ".signature"


def check_expiry():
    """A cached token is reused until it is nearly up, and junk never is."""
    assert not _expired(_token(time.time() + 3600))
    assert _expired(_token(time.time() - 1))
    # Reason: the 30s margin exists so a token cannot lapse mid-request.
    assert _expired(_token(time.time() + 5))
    assert _expired("not-a-jwt")
    assert _expired("")


def check_kind():
    """Type rendering collapses wrappers instead of showing them."""
    assert kind({"type": "string"}) == "string"
    assert kind({"type": "array", "items": {"type": "object"}}) == "array[object]"
    assert kind({"allOf": [{"type": "integer"}]}) == "integer"
    assert kind({"enum": ["a", "b"]}) == "enum"
    assert kind({"properties": {}}) == "object"


def check_resolve_cycle():
    """Mutually recursive schemas terminate instead of hanging."""
    schemas = {
        "Person": {
            "type": "object",
            "properties": {"events": {"$ref": "#/components/schemas/Event"}},
        },
        "Event": {
            "type": "object",
            "properties": {"who": {"$ref": "#/components/schemas/Person"}},
        },
    }
    out = resolve(schemas["Person"], schemas, ("Person",))
    assert out["properties"]["events"]["properties"]["who"] == "<Person>"


def check_dig():
    """Dotted paths walk through arrays as well as objects."""
    schema = {
        "type": "object",
        "properties": {
            "refs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"role": {"type": "string"}},
                },
            }
        },
    }
    assert dig(schema, ["refs", "role"]) == {"type": "string"}
    try:
        dig(schema, ["nope"])
    except SystemExit as exit_error:
        assert "nope" in str(exit_error)
    else:
        raise AssertionError("digging a missing property should exit")


def check_describe_leaf():
    """Describing a leaf prints its values rather than crashing on no properties."""
    describe({"type": "string", "enum": ["x"], "description": "d"}, "Thing")


if __name__ == "__main__":
    for name, check in sorted(globals().items()):
        if name.startswith("check_"):
            check()
            print(f"ok  {name}")
    print("all checks passed")
