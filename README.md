# Gramps Skill

An agent skill for researching and editing a family tree hosted on
[Gramps Web](https://www.grampsweb.org/).

A `SKILL.md`, three standard-library Python scripts, and a place to record your
tree's conventions.

## Install

Clone it where your agent looks for skills:

```bash
git clone https://github.com/cabout-me/gramps-skill ~/.claude/skills/gramps
```

Set three variables, in the environment or a `.env` file at the repo root:

```
GRAMPS_API_URL=https://your-instance.example.com
GRAMPS_USERNAME=you
GRAMPS_PASSWORD=...
```

Any `python3` runs the scripts.

## Contents

```
skills/gramps/
  SKILL.md              genealogy practice, and the API behaviour worth knowing
  scripts/api.py        authenticated passthrough; any endpoint, any method
  scripts/spec.py       expands schemas from the live OpenAPI spec
  scripts/selfcheck.py  offline checks; no network, no credentials
  house-rules/          your tree's conventions
  references/dates.md   Gramps date integer codes
```

`api.py` is the way in and out:

```bash
scripts/api.py GET  people/ -p page=1 -p pagesize=10
scripts/api.py GET  people/{handle} -p profile=self,events -p keys=profile
scripts/api.py POST media/ -f scan.pdf
scripts/api.py PUT  people/{handle} -b @person.json
```

Browse the API with `jq` against the spec your instance publishes:

```bash
jq -r '.paths | keys[]' $(scripts/spec.py --file)
```

`spec.py` covers what `jq` cannot: Gramps schemas are mutually recursive, so
inlining `Person` yields 59 KB where a summary is 2 KB.

## Scope

Gramps Web ships a read-only AI assistant for answering questions about a tree.
This skill covers writing to one: creating and correcting records, sourcing
them, and following the Repository-Source-Citation-Event chain.

## House rules

Each tree has conventions: how notes are worded, how media are named, which
fields stay empty. `house-rules/README.md` explains how to derive them from your
own data by counting, so a rule carries its evidence. Derived rules describe a
family tree rather than this software, so they are gitignored.

## Development

```bash
uv sync
uv run pre-commit install
python3 skills/gramps/scripts/selfcheck.py
```

`selfcheck.py` covers the logic that is not HTTP -- JWT expiry, recursive schema
resolution, path walking -- and needs no network or credentials.

Two rules:

- **The scripts stay standard-library only.** A dependency is something that has
  to be installed wherever the skill runs.
- **Link upstream documentation, never vendor it.** A checked-in copy goes stale
  without telling you, and may not be yours to redistribute.

## Licence

MIT. See [LICENSE](LICENSE).
