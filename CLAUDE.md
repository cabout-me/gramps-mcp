### What this is

An agent skill for a Gramps Web family tree, in `skills/gramps/`. Read
`README.md` and `skills/gramps/SKILL.md` before changing anything.

### The governing rule

**This repo holds only what the Gramps Web API cannot do for itself.** The API
validates its own input, selects its own fields, filters its own queries and
reports its own errors. What remains is credentials, genealogy practice, and the
behaviour worth knowing about.

Before adding code, check whether a query parameter already does the job --
`keys`, `skipkeys`, `profile`, `extend`, `gql`. Usually one does.

### Scripts

- **Standard library only.** The skill runs wherever `python3` does, without an
  install step.
- `api.py` is the only thing that talks to the API or holds a credential.
- `spec.py` covers what `jq` cannot: `$ref` inlining with cycle detection, since
  Gramps schemas are mutually recursive.
- Keep files short, with Google-style docstrings.

### Verifying

- `python3 skills/gramps/scripts/selfcheck.py` runs offline without credentials
  and covers the non-HTTP logic. Extend it when you add logic of that kind.
- Everything else is checked against a real instance, with real API calls.
- **Read the spec before probing the server.** Parameter behaviour is documented
  precisely in `openapi.json`; a probe tells you about one case.

### Documentation

- **Link upstream docs, never vendor them.** A checked-in copy goes stale
  silently, and `gramps-web-docs` declares no licence. Point at the live spec
  and the live user guide.
- `references/` holds only what has no live source -- currently the Gramps date
  integer codes, which come from Gramps core.

### House rules

`skills/gramps/house-rules/` holds per-tree conventions. The mechanism
(`README.md`) is committed; derived rules are gitignored, since they describe
someone's family tree. Rules carry their evidence and the query that produced
them, so they can be re-derived.

### Conventions

- Use `uv run` for tooling; `uv run git commit` so pre-commit runs.
- MIT licensed, no per-file licence headers.
- No emojis in code or docs; pre-commit enforces it.
