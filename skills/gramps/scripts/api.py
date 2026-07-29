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
Authenticated passthrough to the Gramps Web API.

Any endpoint, any method. The API validates its own input and reports its own
errors -- this only attaches a token.

    api.py GET people/ -p pagesize=5 -p 'gql=surname=Smith'
    api.py GET people/{handle} -p profile=all -p extend=all
    api.py POST people/ -b '{"primary_name": {"first_name": "Jan"}}'
    api.py PUT people/{handle} -b @person.json
    api.py POST media/ -f scan.pdf

Config comes from the environment, falling back to a .env file found by walking
up from this script: GRAMPS_API_URL, GRAMPS_USERNAME, GRAMPS_PASSWORD.
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "gramps"
TOKEN_FILE = CACHE / "token"


def config():
    """
    Read connection settings from the environment.

    Returns:
        tuple[str, str, str]: API base URL (ending in /api), username, password.
    """
    if not os.environ.get("GRAMPS_API_URL"):
        for parent in Path(__file__).resolve().parents:
            env_file = parent / ".env"
            if env_file.is_file():
                for line in env_file.read_text().splitlines():
                    key, sep, value = line.partition("=")
                    key = key.strip()
                    if sep and key and not key.startswith("#"):
                        os.environ.setdefault(key, value.split(" #")[0].strip())
                break
    try:
        url = os.environ["GRAMPS_API_URL"].rstrip("/")
        url = url if url.endswith("/api") else url + "/api"
        return url, os.environ["GRAMPS_USERNAME"], os.environ["GRAMPS_PASSWORD"]
    except KeyError as missing:
        sys.exit(
            f"missing {missing}: set GRAMPS_API_URL, GRAMPS_USERNAME, GRAMPS_PASSWORD"
        )


def _request(method, url, data=None, headers=None):
    """Send one HTTP request, returning (status, body, headers) even for errors."""
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as error:
        return error.code, error.read(), dict(error.headers)
    except urllib.error.URLError as error:
        sys.exit(f"cannot reach {url}: {error.reason}")


def _login(base, username, password):
    """Exchange credentials for a JWT and cache it for later invocations."""
    status, body, _ = _request(
        "POST",
        f"{base}/token/",
        json.dumps({"username": username, "password": password}).encode(),
        {"Content-Type": "application/json"},
    )
    if status != 200:
        sys.exit(f"login failed ({status}): {body.decode(errors='replace')}")
    token = json.loads(body)["access_token"]
    CACHE.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Reason: create with 0600 rather than chmod after, so the token is never
    # world-readable, not even briefly.
    fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(token)
    return token


def _expired(token):
    """Check a cached JWT's exp claim. The server verifies the signature."""
    try:
        payload = token.split(".")[1]
        claims = json.loads(
            base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        )
        return claims.get("exp", 0) - time.time() < 30
    except Exception:
        return True


def call(method, endpoint, params=None, body=None, content_type="application/json"):
    """
    Make an authenticated call to the Gramps Web API.

    Args:
        method (str): HTTP method.
        endpoint (str): Path below /api, e.g. "people/" or "people/abc/timeline".
        params (dict | None): Query parameters.
        body (object | bytes | None): JSON body, or raw bytes to send verbatim.
        content_type (str): Content-Type header; set this when body is bytes.

    Returns:
        tuple[int, object, dict]: HTTP status, decoded response, response headers.
    """
    base, username, password = config()
    token = TOKEN_FILE.read_text().strip() if TOKEN_FILE.is_file() else ""
    if not token or _expired(token):
        token = _login(base, username, password)

    url = f"{base}/{endpoint.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    # Reason: media upload POSTs the file itself, not JSON describing it, so
    # bytes pass through untouched with the file's own Content-Type.
    if isinstance(body, bytes):
        data = body
    elif body is not None:
        data = json.dumps(body).encode()
    else:
        data = None
    headers = {"Authorization": f"Bearer {token}", "Content-Type": content_type}

    status, raw, received = _request(method, url, data, headers)
    if status == 401:
        # Reason: cached token was rejected (revoked, or the server restarted
        # with a new secret) even though its exp looked fine.
        headers["Authorization"] = f"Bearer {_login(base, username, password)}"
        status, raw, received = _request(method, url, data, headers)

    try:
        return status, json.loads(raw), received
    except ValueError:
        return status, raw.decode(errors="replace"), received


def main():
    """Run one API call from the command line."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("method", help="GET, POST, PUT, DELETE")
    parser.add_argument("endpoint", help="path below /api, e.g. people/")
    parser.add_argument(
        "-p", "--param", action="append", default=[], metavar="KEY=VALUE"
    )
    parser.add_argument("-b", "--body", help="JSON string, @file, or @- for stdin")
    parser.add_argument("-f", "--file", help="upload this file's bytes as the body")
    args = parser.parse_args()

    params = dict(item.split("=", 1) for item in args.param)
    body = None
    content_type = "application/json"
    if args.file:
        body = Path(args.file).read_bytes()
        content_type = mimetypes.guess_type(args.file)[0] or "application/octet-stream"
    elif args.body:
        text = args.body
        if text.startswith("@"):
            text = sys.stdin.read() if text == "@-" else Path(text[1:]).read_text()
        body = json.loads(text)

    status, result, received = call(
        args.method.upper(), args.endpoint, params, body, content_type
    )
    print(result if isinstance(result, str) else json.dumps(result, indent=2))
    # Reason: list endpoints report the unpaginated total only in this header,
    # so it is invisible unless surfaced. stderr keeps stdout valid JSON.
    total = received.get("X-Total-Count")
    if total is not None:
        print(f"X-Total-Count: {total}", file=sys.stderr)
    sys.exit(0 if status < 400 else 1)


if __name__ == "__main__":
    main()
