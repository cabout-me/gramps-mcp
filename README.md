# Gramps Skill

An agent skill for researching and editing a family tree hosted on
[Gramps Web](https://www.grampsweb.org/).

It is a `SKILL.md`, three standard-library Python scripts, and a place to record
your tree's own conventions. There is no server, no container, and nothing to
install.

## Why there is no MCP server any more

This repository used to be `gramps-mcp`: an MCP server exposing 16 tools over
~7,000 lines that mirrored the Gramps Web API. Two things made that mirror
unnecessary.

**Gramps Web answers questions itself.** Since API v3.6.0 it ships a read-only
AI assistant with its own tools for searching and filtering your tree. If you
want to ask questions, use that -- it is closer to the data and maintained by
the people who own it. This skill exists for the part it deliberately does not
do: **writing**.

**Every instance describes itself.** Since v3.8 the API generates
`openapi.json` from its own code and serves it unauthenticated. A vendored copy
of the API surface is not just redundant, it is worse -- it goes stale silently,
and this one had drifted into rejecting values the server accepts.

What was left after removing everything the API can do for itself is
credentials, genealogy practice, and the traps. That is the skill.

## Install

Clone it where your agent looks for skills, for example:

```bash
git clone https://github.com/cabout-me/gramps-skill ~/.claude/skills/gramps
```

Then set three variables, in the environment or a `.env` file at the repo root:

```
GRAMPS_API_URL=https://your-instance.example.com
GRAMPS_USERNAME=you
GRAMPS_PASSWORD=...
```

That is the whole setup. The scripts use only the standard library, so any
`python3` will run them.

## What is in it

```
skills/gramps/
  SKILL.md              genealogy practice, and the API behaviour worth knowing
  scripts/api.py        authenticated passthrough; any endpoint, any method
  scripts/spec.py       expands schemas from the live OpenAPI spec
  scripts/selfcheck.py  offline checks; no network, no credentials
  house-rules/          your tree's conventions (see below)
  references/dates.md   Gramps date integer codes
```

`api.py` is the only way in and out:

```bash
scripts/api.py GET  people/ -p page=1 -p pagesize=10
scripts/api.py GET  people/{handle} -p profile=self,events -p keys=profile
scripts/api.py POST media/ -f scan.pdf
scripts/api.py PUT  people/{handle} -b @person.json
```

For browsing the API, use `jq` against the spec your own instance publishes:

```bash
jq -r '.paths | keys[]' $(scripts/spec.py --file)
```

`spec.py` handles only what `jq` is bad at -- Gramps schemas are mutually
recursive, so inlining `Person` naively produces 59 KB where a summary is 2 KB.

## House rules

Every tree has conventions that exist nowhere in Gramps or its API: how notes
are worded, how media are named, which fields are deliberately empty. Records
that ignore them are valid and visibly wrong, and nothing errors.

`house-rules/README.md` explains how to derive them from your own data by
counting, so a rule carries its evidence. The derived rules describe your
family tree rather than this software, so they are gitignored -- only the
mechanism ships.

## Development

```bash
uv sync
uv run pre-commit install
python3 skills/gramps/scripts/selfcheck.py
```

`selfcheck.py` covers the logic that is not just HTTP -- JWT expiry, recursive
schema resolution, path walking. It needs no network and no credentials.

Two rules worth keeping:

- **The scripts stay standard-library only.** A dependency is a thing that has
  to be installed wherever the skill runs.
- **Do not vendor upstream documentation.** Link to it. A checked-in copy goes
  stale without telling you, and may not be yours to redistribute.

## Licence

MIT. See [LICENSE](LICENSE).

Earlier versions were AGPL-3.0; `v1.1.0` is the last release under it and the
last with the MCP server.
