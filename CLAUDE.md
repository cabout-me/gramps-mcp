### What this repository is

An agent skill for a Gramps Web family tree, in `skills/gramps/`. It is not a
Python package and not a server. It used to be an MCP server; that was deleted
because Gramps Web ships its own read-only assistant and publishes
`openapi.json` from the running code. **Do not reintroduce a server, a tool
registry, or a Pydantic model of the API.**

Read `README.md` and `skills/gramps/SKILL.md` before changing anything.

### The governing rule

**This repo only contains what the Gramps Web API cannot do for itself.** It
validates its own input, selects its own fields, filters its own queries and
reports its own errors. Duplicating any of that is how the previous design
rotted: hand-transcribed enums drifted until they rejected values the server
accepts.

Before adding code, check whether a query parameter already does it -- `keys`,
`skipkeys`, `profile`, `extend`, `gql`. Usually one does.

### Scripts

- **Standard library only.** No httpx, no pydantic, no PyJWT. The skill has to
  run wherever `python3` does, without an install step.
- `api.py` is the only thing that talks to the API or holds a credential.
- `spec.py` handles only what `jq` cannot: Gramps schemas are mutually
  recursive, so `$ref` inlining needs cycle detection.
- Keep files short and functions documented Google-style, as before.

### Verifying

- `python3 skills/gramps/scripts/selfcheck.py` -- offline, no credentials,
  covers the non-HTTP logic. Extend it when you add logic of that kind.
- Everything else is checked against a real instance. There are no mocks and no
  pytest suite.
- **Before writing to a tree, read the spec, not the server.** Query parameter
  behaviour is documented precisely in `openapi.json`; probing endpoints to
  find out is slower and tells you about one case instead of the rule.

### Documentation

- **Never vendor upstream docs.** Link to them. A checked-in copy goes stale
  silently, and `gramps-web-docs` declares no licence, so copying it is not
  ours to redistribute. Point at the live spec and the live user guide.
- `references/` is only for things with no live source -- currently the Gramps
  date integer codes, which come from Gramps core rather than the web API.

### House rules

`skills/gramps/house-rules/` holds per-tree conventions. The mechanism
(`README.md`) is committed; derived rules are gitignored because they describe
someone's family tree, not this software. Rules carry their evidence and the
query that produced them, so they can be re-derived rather than trusted.

### Conventions

- Use `uv run` for tooling; `uv run git commit` so pre-commit runs.
- MIT licensed. **No per-file licence headers** -- the hook that added them was
  removed with the AGPL relicence.
- No emojis in code or docs; pre-commit enforces it.
