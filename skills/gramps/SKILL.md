---
name: gramps
description: Read and write a family tree hosted on Gramps Web. Use when the user asks to look up, add, correct, or source people, families, events, places, sources, citations, notes or media in their genealogy database, or to research their own tree.
---

# Gramps Web

Your tree lives behind the Gramps Web API. One script calls it; the API
validates its own input, selects its own fields and reports its own errors.
This skill carries only what the API cannot: credentials, and genealogy
practice.

Gramps Web ships its own read-only assistant for answering questions. This
skill is for the other half -- writing to the tree.

## Setup

Three environment variables, or a `.env` file at the repo root:

```
GRAMPS_API_URL=https://your-instance.example.com
GRAMPS_USERNAME=you
GRAMPS_PASSWORD=...
```

Stdlib only, no install step.

## Read the spec first

Every Gramps Web instance publishes a complete, auto-generated OpenAPI spec at
`/api/openapi.json`, unauthenticated. Since v3.8 it is generated from the
running code specifically so agents can trust it. It describes all 183
operations with every parameter and what each one does.

**When you have a question about an endpoint or a parameter, the spec answers
it. Read it before you experiment** -- a probe costs a round trip and tells you
about one case; the spec tells you the rule.

Browse it with `jq`:

```bash
SPEC=$(scripts/spec.py --file)          # downloads and caches, prints the path

# what operations exist
jq -r '.paths | keys[]' $SPEC
jq -r '.paths | keys[] | select(contains("citation"))' $SPEC

# which methods a path allows
jq -r '.paths."/api/people/{handle}" | keys[]' $SPEC

# what a parameter actually does -- read the description, it is precise
jq -r '.paths."/api/people/".get.parameters[] | "\(.name): \(.description)"' $SPEC

# which endpoints accept a given parameter
jq -r '.paths | to_entries[] | select(.value.get.parameters) | .key as $p
       | .value.get.parameters[] | select(.name=="gql") | $p' $SPEC
```

Object shapes need `scripts/spec.py`, because Gramps schemas are mutually
recursive and jq cannot inline them without looping:

```bash
scripts/spec.py Person                 # fields, one line each
scripts/spec.py Person.primary_name    # drill into a field
scripts/spec.py Event.date --full      # raw JSON for a fragment
```

Two things the spec does not cover, so get them elsewhere:

- **Request bodies for POST and PUT are undocumented.** Use `spec.py Person`
  for the shape, or `GET` an existing record and mirror it.
- **Valid type strings** live in the database: `scripts/api.py GET types/`.

## Calling the API

```bash
scripts/api.py GET  people/ -p page=1 -p pagesize=10
scripts/api.py GET  people/{handle} -p profile=self,events -p keys=profile
scripts/api.py POST notes/ -b '{"text": {"string": "..."}, "type": "Transcript"}'
scripts/api.py PUT  people/{handle} -b @person.json
```

`-p` repeats for query parameters. `-b` takes a JSON string, `@file`, or `@-`
for stdin. `X-Total-Count` goes to stderr, since the body never tells you how
many matches exist beyond the page you asked for.

**Read the response before acting on it.** A successful list call returns a JSON
array; a failed one returns an object with an `error` key naming the field:

```
{"error": {"code": 422, "message": "query: keys: Unknown field."}}
```

Both are truthy and both have a length, so check for `error` before you count
results or index into them. When a call goes wrong the message usually says
exactly what to fix.

## Keeping responses small

**Always send `page` together with `pagesize`.** The spec is explicit: *"page:
If omitted, all results are returned"*, and pagesize applies only *"when
pagination is active"*. On a 4,000-person tree, `pagesize=5` alone returns all
4,463 records.

```
-p pagesize=5 -p page=1    -> 5 records
-p page=1                  -> 20 records (default page size)
-p pagesize=5              -> everything
```

**Let the API do the trimming.** It resolves handles into names, ISO dates and
full place names server-side, which is almost always the readable form you
wanted:

```bash
scripts/api.py GET people/{handle} -p profile=self,events -p keys=profile
```

Name the profile sections you need -- `self`, `events`, `families`, `age`,
`span`, `ratings`, `references`, `participants`. **Prefer these to `all`**:
`all` recursively embeds relatives' full profiles, which on a person with 14
events is 41.6 KB against 4.4 KB for `self,events` carrying the same readable
content.

Also available: `keys=handle,gramps_id` to whitelist fields, `skipkeys=` to
drop noisy ones, `extend=` to inline referenced objects (expensive -- reach for
`profile` first).

## Searching

Two mechanisms, for different questions.

**`-p 'gql=...'` filters on structure** -- use it when you know the field. A
query is one or more `field operator value` tests joined with `and` / `or`, with
parentheses where needed. Operators: `=`, `!=`, `~` (contains), `!~`, `>`, `<`.

Reaching into a list needs `any` or `all` at the point where the list is
indexed, and following a handle to another object needs a `get_*` step:

```bash
scripts/api.py GET people/ -p 'gql=primary_name.surname_list.any.surname ~ Dobrzy' \
                           -p page=1 -p pagesize=10
scripts/api.py GET events/ -p 'gql=place.get_place.name.value ~ Vrasene' \
                           -p page=1 -p pagesize=10
```

Quote values containing spaces or punctuation, or the parser stops at the first
odd character and returns a 422 pointing at the column.

**The full property list is on the instance's own docs site** --
<https://www.grampsweb.org/user-guide/gql/>. Read it there rather than guessing
a path: a wrong path is an error, not a near miss, and property names rarely
match the field names you see in a response. It is not part of `openapi.json`,
so nothing local can tell you.

**`GET search/ -p query=...` matches text anywhere**, notes included. Use it
when you know a phrase but not a field. Its results are wrapped differently --
each item is `{"object_type": "person", "object": {...}}` rather than the object
itself.

## Writing

### Always find first

**Search before creating anything** -- repository, source, citation, place,
event, person, family. Every one of them. Duplicates are the most common damage
an assistant does to a tree and the most tedious to undo, and each link in the
chain below is a chance to make one.

Each search has three outcomes, and they are three different actions:

| Search result | Do this |
|---|---|
| Found, and it already has the new information | Use it as-is. Write nothing. |
| Found, but missing some of the information | `PUT` the existing handle -- read, edit, write |
| Not found | `POST` a new one |

The middle row is the one that gets skipped, and skipping it is how you get two
"St. Mary's Church" records where one should have gained an address.

**When a search returns a plausible match, show it to the user and ask.** Do
not decide identity alone -- "same Jan Kowalski or a different one?" is a
research judgement, not a lookup. Present what you found, say what matches and
what does not, and wait.

### Read the house rules first

Every tree has conventions that exist nowhere in Gramps, the API or this file:
how notes are worded, how media are named, which fields are deliberately empty,
whether repositories are used at all. Records that ignore them are valid and
visibly wrong, and nothing errors.

**Read `house-rules/` before your first write in a session.** If there is no
rules file for this tree, derive one -- `house-rules/README.md` has the queries
-- and offer to save it.

What this catches, from a real tree: citation notes that contain **only a URL**,
where a well-meaning prose citation would have been the odd one out in 2,053;
media named by **document-type code** (`HA` huwelijksakte, `GA` geboorteakte,
`OA` overlijdensakte) where a descriptive title breaks sorting across 800 files;
and uncertainty expressed through `modifier` with `quality` **always 0**, so an
`estimated` date would have been the only one in 8,375 events.

When the rules do not cover your case, look at siblings of the thing you are
about to create -- another citation on the same source, another media item of
the same type -- and copy what you see. When they disagree, show the user two
examples and ask which to follow, then write the answer into the rules file.

The data is the authority; `house-rules/` is a cache of it. Re-derive rather
than trust a rule that seems to fight what you are seeing.

### The chain

Gramps is source-focused and event-focused. Facts hang off events, events are
backed by citations, citations point at sources, sources sit in repositories.
Build in that order -- each step needs a handle from the one before:

```
Repository -> Source -> Citation -> Event <- Person / Family
```

A birth date is not a field on a person. It is a Birth event, cited to a
document, with the person referencing it. Same for death, baptism, burial.

### Creating

Required fields are minimal: a person needs `primary_name` and `gender`
(0 female, 1 male, 2 unknown, 3 other). `_class` is optional on create -- the
endpoint determines the type. Everything else can be added later.

A POST returns a **transaction list, not the object**:

```json
[{"type": "add", "_class": "Note", "handle": "103cd...", "old": null,
  "new": {"gramps_id": "N1692", "handle": "103cd...", ...}}]
```

Take the handle from `[0]["handle"]`. Creating a family returns several entries
-- the family plus every person it touched -- so match
`entry["_class"] == "Family"` rather than assuming the first entry.

### Use exact type strings

Type fields accept a string, and **an unrecognised string is accepted as a
custom type rather than rejected**. `"Transcript"` becomes `{"value": 3}`;
`"transcript"` becomes `{"value": 0, "string": "transcript"}` -- a new custom
type, silently. They are case-sensitive and there is no error to catch it.

So take type strings verbatim from the database:

```bash
scripts/api.py GET types/          # {"default": {...}, "custom": {...}}
```

### Events attach to people, not the reverse

An event does not list its participants. Each person carries an
`event_ref_list` entry pointing at it, with that person's role:

```json
{"ref": "<event handle>", "role": "Primary"}
```

Linking a person to an event is therefore *an update to the person*. Roles like
"Groom", "Bride", "Witness" live in the same place.

Individual events (birth, death, baptism, burial) attach to the person; family
events (marriage, divorce, engagement) attach to the family.

`birth_ref_index` and `death_ref_index` are **positions within
`event_ref_list`**, not handles. When you append a birth event, set
`birth_ref_index` to its index in the same write, or it will not read as a
birth. `-1` means none.

### Updating is read, edit, write

`PUT` replaces the whole object. Fetch the raw record -- no `profile`, no
`keys` -- change what you mean to change, send it all back:

```bash
scripts/api.py GET people/{handle} > /tmp/person.json
# edit: append to event_ref_list, keep every other field
scripts/api.py PUT people/{handle} -b @/tmp/person.json
```

Any field you leave out is dropped, silently.

### Media is uploaded as bytes, and named in a second pass

Media is the one endpoint that does not take JSON. `POST media/` sends the file
itself, with its own Content-Type:

```bash
scripts/api.py POST media/ -f scan.pdf
```

The server checksums the file, stores it as `<checksum><ext>`, and creates the
object pointing there with an empty `desc`. You cannot name it up front -- the
object does not exist until the bytes arrive.

To give it a real name, three calls:

```bash
scripts/api.py POST media/ -f scan.pdf                    # 1. creates the object
# 2. GET it, set desc and path, PUT it back (leave checksum alone)
scripts/api.py PUT media/{handle}/file -p uploadmissing=true -f scan.pdf   # 3.
```

Step 3 is what actually moves the file. The server sees a matching checksum and
no file at the object's new path, so it writes the bytes there instead of
generating a fresh name. **Changing `path` without step 3 leaves the object
pointing at nothing** -- files are served through `path`, not the checksum.

Confirm it worked by fetching the file, not just the record:

```bash
scripts/api.py GET media/{handle} -p keys=path,desc,checksum
# then GET media/{handle}/file -- expect 200 and the original byte count
```

The first upload's checksum-named file stays on disk unreferenced. The API has
no endpoint for deleting orphaned files, so removing it needs shell access to
the server. Worth mentioning to the user rather than leaving silently behind.

### Places nest

A place carries a `placeref_list` pointing at whatever encloses it: church in
city in county in state in country. Build upward until you reach an existing
place, and reuse rather than duplicating -- one "Boston" per tree.

### Dates

Dates are structured. `dateval` is `[day, month, year, slash]` -- day first,
`0` for unknown parts. `modifier`, `quality` and `calendar` are integer codes:
see `references/dates.md`.

## Link what you report

**Whenever you name a record, link it.** The user needs to see it in Gramps Web
to judge whether you got it right, and hunting for `I3342` by hand is friction
that stops them checking.

The web UI takes the **Gramps ID**, not the handle -- same host as the API,
without `/api`:

```
https://<your-instance>/person/I3342
https://<your-instance>/family/F1287
https://<your-instance>/event/E6770
https://<your-instance>/citation/C1434
```

Routes: `person`, `family`, `event`, `place`, `source`, `citation`,
`repository`, `media`, `note`. Deleting an object redirects to the same
pattern, so it is stable.

This matters most before a write: link the records you are about to change and
say what you intend to change about each, so the user can look before saying
yes rather than after.

## Checking your work

**Verify with a number the API computes, not one you derive.** Object counts
are authoritative and cheap:

```bash
scripts/api.py GET metadata/     # object_counts: people, events, notes, ...
```

Counting the length of a search response instead can mislead -- an error object
has a length too, and a filter you got slightly wrong returns a plausible
number rather than a complaint.

## Undo

Gramps keeps a server-side transaction log:

```bash
scripts/api.py GET transactions/history/ -p page=1 -p pagesize=5
```

A safety net for when a write goes wrong -- worth knowing it is there, and
still worth reading a diff before sending it.
